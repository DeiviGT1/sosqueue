import json

class JobService:
    """
    Servicio simplificado que solo gestiona un contador de trabajos.
    """
    def __init__(self):
        self._job_count = 0

    def increment_job_count(self):
        """Suma 1 al contador de trabajos."""
        self._job_count += 1

    def get_job_count(self):
        """Devuelve el número actual de trabajos."""
        return self._job_count

    def decrement_job_count(self):
        """Resta 1 al contador de trabajos, sin bajar de cero."""
        if self._job_count > 0:
            self._job_count -= 1

class QueueService:
    """
    Gestiona las colas de usuarios (disponibles, trabajando, descanso) en memoria.
    """
    def __init__(self):
        self._available_users = []
        self._working_users = []
        self._idle_users = []

    def _find_user_in_queue(self, user_id, queue):
        """Busca un usuario por ID en una cola específica."""
        for user in queue:
            if user.get('id') == user_id:
                return user
        return None

    def _remove_user_from_all_queues(self, user_id):
        """Elimina a un usuario de todas las colas para evitar duplicados."""
        self._available_users = [u for u in self._available_users if u['id'] != user_id]
        self._working_users = [u for u in self._working_users if u['id'] != user_id]
        self._idle_users = [u for u in self._idle_users if u['id'] != user_id]

    def join_available(self, user):
        """Añade un usuario a la cola de disponibles si no está en ninguna otra."""
        self._remove_user_from_all_queues(user.id)
        user_data = {'id': user.id, 'name': user.name}
        self._available_users.append(user_data)

    def move_to_working(self, user_id):
        """Mueve un usuario de 'available' a 'working'."""
        user = self._find_user_in_queue(user_id, self._available_users)
        if user:
            self._available_users.remove(user)
            self._working_users.append(user)
            return True
        return False

    def move_to_idle(self, user_id):
        """Mueve un usuario desde cualquier cola activa a 'idle'."""
        user = self._find_user_in_queue(user_id, self._available_users)
        if user:
            self._available_users.remove(user)
            self._idle_users.append(user)
            return

        user = self._find_user_in_queue(user_id, self._working_users)
        if user:
            self._working_users.remove(user)
            self._idle_users.append(user)

    def move_to_available(self, user_id):
        """Mueve a un usuario de vuelta a 'available' desde 'working' o 'idle'."""
        self._remove_user_from_all_queues(user_id)
        user_credentials = UserService.get_user_by_id(user_id)
        if user_credentials:
            self.join_available(user_credentials)

    def get_queue(self, queue_name):
        """Devuelve la cola solicitada."""
        if queue_name == 'sosq:available':
            return self._available_users
        elif queue_name == 'sosq:working':
            return self._working_users
        elif queue_name == 'sosq:idle':
            return self._idle_users
        else:
            raise ValueError(f"Cola desconocida: {queue_name}")

    def get_full_state(self):
        """Devuelve el estado completo de todas las colas."""
        return {
            'available_users': self._available_users,
            'working_users': self._working_users,
            'idle_users': self._idle_users,
        }

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
        from app.models.User import User
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
        from app.models.User import User
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