import os
import redis
from ..models import User # Nos aseguramos de importar la CLASE User directamente

# --- JobService ---
class JobService:
    def __init__(self):
        self.redis_client = None
        try:
            redis_url = os.environ.get("REDIS_URL")
            if not redis_url:
                print("ERROR CRÍTICO: No se pudo conectar con Redis para JobService. La variable de entorno REDIS_URL no está configurada.")
                return
            self.redis_client = redis.from_url(redis_url)
        except Exception as e:
            print(f"ERROR CRÍTICO: No se pudo conectar con Redis para JobService. {e}")

    def get_job_count(self):
        if not self.redis_client:
            return 0
        job_count = self.redis_client.get('sosq:job_count')
        return job_count.decode('utf-8') if job_count else 0

# --- QueueService ---
class QueueService:
    def __init__(self):
        self.redis_client = None
        try:
            redis_url = os.environ.get("REDIS_URL")
            if not redis_url:
                print("ERROR CRÍTICO: No se pudo conectar con Redis. La variable de entorno REDIS_URL no está configurada.")
                return
            self.redis_client = redis.from_url(redis_url, ssl_cert_reqs=None, decode_responses=True)
        except Exception as e:
            print(f"ERROR CRÍTICO: No se pudo conectar con Redis. {e}")

    def get_available_users(self):
        if not self.redis_client: return []
        return self.redis_client.lrange('sosq:available', 0, -1)

    def get_working_users(self):
        if not self.redis_client: return []
        return self.redis_client.lrange('sosq:working', 0, -1)

    def get_idle_users(self):
        if not self.redis_client: return []
        return self.redis_client.lrange('sosq:idle', 0, -1)

    def add_user_to_available(self, user):
        if not self.redis_client: return
        self.redis_client.rpush('sosq:available', user.id)

    def move_user_to_working(self, user_id):
        if not self.redis_client: return
        self.redis_client.lrem('sosq:available', 0, user_id)
        self.redis_client.rpush('sosq:working', user_id)

    def move_user_to_idle(self, user_id):
        if not self.redis_client: return
        self.redis_client.lrem('sosq:working', 0, user_id)
        self.redis_client.rpush('sosq:idle', user_id)

    def move_user_to_available(self, user_id, queue_name):
        if not self.redis_client: return
        if queue_name == 'working':
            self.redis_client.lrem('sosq:working', 0, user_id)
        elif queue_name == 'idle':
            self.redis_client.lrem('sosq:idle', 0, user_id)
        self.redis_client.rpush('sosq:available', user_id)

    def remove_user_from_all_queues(self, user_id):
        if not self.redis_client: return
        self.redis_client.lrem('sosq:available', 0, user_id)
        self.redis_client.lrem('sosq:working', 0, user_id)
        self.redis_client.lrem('sosq:idle', 0, user_id)

# --- UserService ---
class UserService:
    # La definición de la lista de usuarios debe ser un atributo de clase
    _users = [
        User(id='1', name='Juanfer', pin='1234'),
        User(id='2', name='David', pin='5678'),
    ]

    @classmethod
    def get_all(cls):
        return cls._users

    @classmethod
    def get(cls, id):
        return next((user for user in cls._users if user.id == id), None)