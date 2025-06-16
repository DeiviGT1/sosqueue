import os
import json
import redis
from app.models.User import User

class JobService:
    """Gestiona el contador de trabajos pendientes usando Redis."""
    def __init__(self):
        self.job_key = 'sosqueue_job_count'
        self.db = None
        try:
            redis_url = os.environ.get("REDIS_URL")
            if not redis_url:
                raise ValueError("La variable de entorno REDIS_URL no está configurada.")
            self.db = redis.from_url(redis_url, decode_responses=True)
            self.db.ping()
        except Exception as e:
            print(f"ERROR CRÍTICO: No se pudo conectar con Redis para JobService. {e}")

    def get_job_count(self):
        """Devuelve el número de trabajos disponibles."""
        if not self.db: return 0
        count = self.db.get(self.job_key)
        return int(count) if count else 0

class QueueService:
    """Gestiona TODAS las colas de usuarios (available, working, idle)."""
    def __init__(self):
        self._available_users = []
        self._working_users = []
        self._idle_users = []
        self.db = None
        try:
            redis_url = os.environ.get("REDIS_URL")
            if not redis_url:
                raise ValueError("La variable de entorno REDIS_URL no está configurada.")
            self.db = redis.from_url(redis_url, decode_responses=True)
            self.db.ping()
        except Exception as e:
            print(f"ERROR CRÍTICO: No se pudo conectar con Redis. {e}")
            
    def _get_user_from_queues(self, user_id, queues):
        """Busca un usuario en una lista de colas."""
        if not self.db: return None, None
        for queue in queues:
            for item_json in self.db.lrange(queue, 0, -1):
                if json.loads(item_json).get('id') == user_id:
                    return item_json, queue
        return None, None

    def get_queue(self, queue_name):
        """Devuelve una cola específica como una lista de diccionarios."""
        if not self.db: return []
        return [json.loads(item) for item in self.db.lrange(queue_name, 0, -1)]

    def join_available(self, user):
        """Añade un usuario a la cola de disponibles si no existe."""
        if not self.db or not user: return
        
        # Evitar duplicados en todas las colas
        all_queues = ['sosq:available', 'sosq:working', 'sosq:idle']
        user_json, _ = self._get_user_from_queues(user.id, all_queues)
        if user_json:
            return

        user_data = {'id': user.id, 'name': user.name, 'pin': user.pin}
        self.db.rpush('sosq:available', json.dumps(user_data))

    def move_to_working(self, user_id):
        """Mueve un usuario de 'available' a 'working'."""
        if not self.db: return
        user_json, queue = self._get_user_from_queues(user_id, ['sosq:available'])
        if user_json:
            self.db.lrem(queue, 1, user_json)
            self.db.rpush('sosq:working', user_json)

    def move_to_idle(self, user_id):
        """Mueve un usuario de 'working' a 'idle'."""
        if not self.db: return
        user_json, queue = self._get_user_from_queues(user_id, ['sosq:working'])
        if user_json:
            self.db.lrem(queue, 1, user_json)
            self.db.rpush('sosq:idle', user_json)

    def move_to_available(self, user_id):
        """Devuelve a un usuario a 'available' desde cualquier otra cola."""
        if not self.db: return
        user_json, queue = self._get_user_from_queues(user_id, ['sosq:working', 'sosq:idle'])
        if user_json:
            self.db.lrem(queue, 1, user_json)
            self.db.rpush('sosq:available', user_json)

    def remove_from_all_queues(self, user_id):
        """Elimina a un usuario de todas las colas."""
        if not self.db: return
        user_json, queue = self._get_user_from_queues(user_id, ['sosq:available', 'sosq:working', 'sosq:idle'])
        if user_json:
            self.db.lrem(queue, 1, user_json)

    def get_full_state(self):
        return {
            'available_users': [user.to_dict() for user in self._available_users],
            'working_users': [user.to_dict() for user in self._working_users],
            'idle_users': [user.to_dict() for user in self._idle_users],
            'job_count': JobService().get_job_count() 
        }
# --- NUEVA CLASE UserService ---
class UserService:
    # Base de datos de usuarios en memoria
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
