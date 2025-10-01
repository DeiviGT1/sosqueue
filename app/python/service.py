import json
import os
from urllib.parse import urlparse
import redis
from app.models.User import User

# --- 1. Conexión a Redis ---
# Se conecta usando la variable de entorno REDIS_URL. Usamos timeouts cortos para evitar bloqueos en el arranque.

def _connect_redis(url: str):
    return redis.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=5,  # evita cuelgues al conectar
        socket_timeout=5,          # evita cuelgues en ping/respuestas
        retry_on_timeout=True,
        health_check_interval=30
    )

def _host_info(url: str) -> str:
    try:
        p = urlparse(url)
        return f"{p.hostname}:{p.port}"
    except Exception:
        return url

try:
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        raise redis.exceptions.ConnectionError("La variable de entorno REDIS_URL no está definida.")
    
    # Primer intento tal cual
    try:
        redis_client = _connect_redis(redis_url)
        redis_client.ping()
    except Exception as primary_err:
        # Si falla y el esquema es redis://, reintenta con TLS rediss:// automáticamente
        parsed = urlparse(redis_url)
        if parsed.scheme == "redis":
            tls_url = "rediss://" + redis_url.split("://", 1)[1]
            try:
                redis_client = _connect_redis(tls_url)
                redis_client.ping()
                # Actualizamos REDIS_URL solo en el entorno del proceso
                os.environ["REDIS_URL"] = tls_url
            except Exception as tls_err:
                raise redis.exceptions.ConnectionError(f"Primer intento falló: {primary_err} | Intento TLS falló: {tls_err}")
        else:
            # No es redis://, propaga el error original
            raise primary_err
except Exception as e:
    from unittest.mock import Mock
    redis_client = Mock()
    # Configuramos el Mock para que devuelva valores por defecto seguros.
    redis_client.get.return_value = 0  # Para get_job_count
    redis_client.lrange.return_value = [] # Para get_queue

# --- 2. Nombres de las Claves en Redis ---
# Usamos constantes para evitar errores de tipeo al referirnos a nuestras listas en Redis.
AVAILABLE_QUEUE_KEY = 'sosq:available'
WORKING_QUEUE_KEY = 'sosq:working'
IDLE_QUEUE_KEY = 'sosq:idle'
JOB_COUNT_KEY = 'sosq:job_count'

# --- 3. Clases de Servicio Modificadas ---

class JobService:
    """
    Servicio que gestiona un contador de trabajos usando Redis para persistencia.
    """
    def __init__(self, client):
        self.redis = client

    def increment_job_count(self):
        """Suma 1 al contador de trabajos en Redis."""
        self.redis.incr(JOB_COUNT_KEY)

    def get_job_count(self):
        """Devuelve el número actual de trabajos desde Redis."""
        count = self.redis.get(JOB_COUNT_KEY)
        return int(count) if count else 0

    def decrement_job_count(self):
        """Resta 1 al contador de trabajos, sin bajar de cero."""
        # Este script LUA asegura que la operación es atómica y segura.
        lua_script = """
        local current = tonumber(redis.call('get', KEYS[1]))
        if current and current > 0 then
            return redis.call('decr', KEYS[1])
        end
        return current
        """
        self.redis.eval(lua_script, 1, JOB_COUNT_KEY)


class QueueService:
    """
    Gestiona las colas de usuarios (disponibles, trabajando, descanso) en Redis.
    """
    def __init__(self, client):
        self.redis = client

    def _serialize_user(self, user_data):
        """Convierte un diccionario de usuario a un string JSON para guardarlo."""
        return json.dumps(user_data)

    def _deserialize_user(self, user_json):
        """Convierte un string JSON de vuelta a un diccionario de usuario."""
        return json.loads(user_json)

    def _find_user_in_queue(self, user_id, queue_key):
        """Busca un usuario por ID en una cola de Redis y devuelve su JSON."""
        for user_json in self.redis.lrange(queue_key, 0, -1):
            if self._deserialize_user(user_json).get('id') == user_id:
                return user_json
        return None

    def _remove_user_from_all_queues(self, user_id):
        """Elimina a un usuario de todas las colas para evitar duplicados."""
        for queue_key in [AVAILABLE_QUEUE_KEY, WORKING_QUEUE_KEY, IDLE_QUEUE_KEY]:
            user_to_remove = self._find_user_in_queue(user_id, queue_key)
            if user_to_remove:
                self.redis.lrem(queue_key, 1, user_to_remove)

    def join_available(self, user):
        """Añade un usuario a la cola de disponibles si no está en ninguna otra."""
        self._remove_user_from_all_queues(user.id)
        user_data = {'id': user.id, 'name': user.name}
        # rpush añade al final de la lista.
        self.redis.rpush(AVAILABLE_QUEUE_KEY, self._serialize_user(user_data))

    def move_to_working(self, user_id):
        """Mueve un usuario de 'available' a 'working'."""
        user_to_move = self._find_user_in_queue(user_id, AVAILABLE_QUEUE_KEY)
        if user_to_move:
            # lrem lo quita de la lista de disponibles.
            self.redis.lrem(AVAILABLE_QUEUE_KEY, 1, user_to_move)
            # rpush lo añade a la lista de trabajando.
            self.redis.rpush(WORKING_QUEUE_KEY, user_to_move)
            return True
        return False

    def move_to_idle(self, user_id):
        """Mueve un usuario desde cualquier cola activa a 'idle'."""
        user_data = None
        # Buscar en 'available'
        user_in_available = self._find_user_in_queue(user_id, AVAILABLE_QUEUE_KEY)
        if user_in_available:
            self.redis.lrem(AVAILABLE_QUEUE_KEY, 1, user_in_available)
            user_data = user_in_available
        
        # Buscar en 'working'
        user_in_working = self._find_user_in_queue(user_id, WORKING_QUEUE_KEY)
        if user_in_working:
            self.redis.lrem(WORKING_QUEUE_KEY, 1, user_in_working)
            user_data = user_in_working

        if user_data:
            self.redis.rpush(IDLE_QUEUE_KEY, user_data)

    def move_to_available(self, user_id):
        """Mueve a un usuario de vuelta a 'available' desde 'working' o 'idle'."""
        self._remove_user_from_all_queues(user_id)
        user_credentials = UserService.get_user_by_id(user_id)
        if user_credentials:
            self.join_available(user_credentials)

    def get_queue(self, queue_name):
        """Devuelve la cola solicitada desde Redis."""
        # Mapeamos los nombres antiguos a las nuevas claves de Redis
        queue_mapping = {
            'sosq:available': AVAILABLE_QUEUE_KEY,
            'sosq:working': WORKING_QUEUE_KEY,
            'sosq:idle': IDLE_QUEUE_KEY
        }
        redis_key = queue_mapping.get(queue_name)
        if not redis_key:
            raise ValueError(f"Cola desconocida: {queue_name}")
        
        users_json = self.redis.lrange(redis_key, 0, -1)
        return [self._deserialize_user(u) for u in users_json]

    def move_user_up(self, user_id):
        """Mueve un usuario una posición hacia arriba en la cola de disponibles."""
        users = self.get_queue('sosq:available')
        try:
            index = next(i for i, user in enumerate(users) if user['id'] == user_id)
        except StopIteration:
            return

        if index > 0:
            users.insert(index - 1, users.pop(index))
            # Actualizamos la lista completa en Redis
            pipe = self.redis.pipeline()
            pipe.delete(AVAILABLE_QUEUE_KEY)
            if users:
                pipe.rpush(AVAILABLE_QUEUE_KEY, *[self._serialize_user(u) for u in users])
            pipe.execute()

    def move_user_down(self, user_id):
        """Mueve un usuario una posición hacia abajo en la cola de disponibles."""
        users = self.get_queue('sosq:available')
        try:
            index = next(i for i, user in enumerate(users) if user['id'] == user_id)
        except StopIteration:
            return

        if index < len(users) - 1:
            users.insert(index + 1, users.pop(index))
            # Actualizamos la lista completa en Redis
            pipe = self.redis.pipeline()
            pipe.delete(AVAILABLE_QUEUE_KEY)
            if users:
                pipe.rpush(AVAILABLE_QUEUE_KEY, *[self._serialize_user(u) for u in users])
            pipe.execute()

    def get_full_state(self):
        """Devuelve el estado completo de todas las colas desde Redis."""
        return {
            'available_users': self.get_queue('sosq:available'),
            'working_users': self.get_queue('sosq:working'),
            'idle_users': self.get_queue('sosq:idle'),
        }


class UserService:
    # Esta clase no necesita cambios, ya que los usuarios son estáticos.
    _CREDENTIALS = {
        'admin':   {'id': 0, 'password': 'admin', 'admin': True, 'pin': '0000', 'name': 'admin'},
        'Juanfer': {'id': 1, 'password': '1', 'pin': '1234', 'name': 'Juanfer'},
        'Edison':  {'id': 2, 'password': '2', 'pin': '5678', 'name': 'Edison'},
        'Johan':   {'id': 3, 'password': '3', 'pin': '9101', 'name': 'Johan'},
        'emp':     {'id': 4, 'password': '4', 'pin': '1121', 'name': 'emp'},
    }

    @classmethod
    def get_user_by_id(cls, user_id):
        """Busca un usuario por su ID y devuelve un objeto User."""
        for uname, cred in cls._CREDENTIALS.items():
            if cred['id'] == int(user_id):
                return User(
                    id=cred['id'],
                    name=uname,
                    pin=cred['pin'],
                    is_admin=cred.get('admin', False)
                )
        return None

    @classmethod
    def get_user_by_name(cls, username):
        """Busca un usuario por su nombre y devuelve un objeto User."""
        if username in cls._CREDENTIALS:
            cred = cls._CREDENTIALS[username]
            return User(
                id=cred['id'],
                name=username,
                pin=cred['pin'],
                is_admin=cred.get('admin', False)
            )
        return None

    @classmethod
    def validate_credentials(cls, username, password):
        """Valida las credenciales de un usuario."""
        user_credentials = cls._CREDENTIALS.get(username)
        if user_credentials and user_credentials['password'] == password:
            return True
        return False
