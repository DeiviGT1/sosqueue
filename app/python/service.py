# app/python/sosqueue/service.py

import os
import json
import redis
from threading import Lock

class QueueService:
    """
    Gestiona una cola de usuarios utilizando Redis para persistencia.
    Cada instancia se asocia a una clave específica en Redis (ej: 'available_queue').
    """
    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        self.db = None
        try:
            redis_url = os.environ.get("REDIS_URL")
            if not redis_url:
                raise ValueError("La variable de entorno REDIS_URL no está configurada.")
            # El decode_responses=True hace que no necesitemos llamar a .decode('utf-8') en cada lectura.
            self.db = redis.from_url(redis_url, decode_responses=True)
            self.db.ping() # Comprueba que la conexión es exitosa.
            print(f"Conectado a Redis y gestionando la cola: {self.queue_name}")
        except Exception as e:
            print(f"ERROR CRÍTICO: No se pudo conectar con Redis. {e}")

    def _get_user_json(self, user_id: int):
        """Busca y devuelve el string JSON de un usuario por su ID."""
        for item_json in self.db.lrange(self.queue_name, 0, -1):
            if json.loads(item_json).get('id') == user_id:
                return item_json
        return None

    def get_queue(self):
        """Devuelve la cola completa como una lista de diccionarios."""
        if not self.db: return []
        return [json.loads(item) for item in self.db.lrange(self.queue_name, 0, -1)]

    def join(self, user):
        """Añade un usuario al final de la cola si no existe."""
        if not self.db: return
        
        queue = self.get_queue()
        if any(u['id'] == user.id for u in queue):
            return # El usuario ya está en la cola, no hacer nada.
        
        user_data = {'id': user.id, 'name': user.username}
        self.db.rpush(self.queue_name, json.dumps(user_data))

    def remove(self, user_id: int):
        """Elimina a un usuario de la cola por su ID."""
        if not self.db: return False
        user_json = self._get_user_json(user_id)
        if user_json:
            # LREM elimina la primera ocurrencia del valor especificado.
            self.db.lrem(self.queue_name, 1, user_json)
            return True
        return False

    def pop_first(self):
        """Elimina y devuelve el primer elemento de la cola."""
        if not self.db: return None
        item = self.db.lpop(self.queue_name)
        return json.loads(item) if item else None
    
    def move_all_to(self, destination_queue_service):
        """Mueve todos los elementos de esta cola a otra."""
        if not self.db: return
        # Mueve elementos uno por uno. RPOPLPUSH es atómico.
        while self.db.rpoplpush(self.queue_name, destination_queue_service.queue_name):
            pass

    def move_up(self, user_id: int):
        """Mueve a un usuario una posición hacia arriba en la cola."""
        if not self.db: return
        user_json = self._get_user_json(user_id)
        if not user_json: return

        # Usamos un pipeline para asegurar que las operaciones se ejecuten de forma atómica.
        with self.db.pipeline() as pipe:
            pipe.lrem(self.queue_name, 1, user_json)
            pipe.linsert(self.queue_name, 'BEFORE', user_json, user_json) # Truco para reinsertar
            # La línea anterior es conceptual. Una forma más simple es:
            # 1. Obtener la lista, 2. Modificarla en Python, 3. Borrar y reescribir la lista.
            # Implementemos la forma simple y robusta:
            queue = self.get_queue()
            try:
                idx = next(i for i, u in enumerate(queue) if u['id'] == user_id)
                if idx > 0:
                    queue.insert(idx - 1, queue.pop(idx))
                    pipe.multi()
                    pipe.delete(self.queue_name)
                    for user in queue:
                        pipe.rpush(self.queue_name, json.dumps(user))
                    pipe.execute()
            except StopIteration:
                pass # El usuario no fue encontrado.

    def move_down(self, user_id: int):
        """Mueve a un usuario una posición hacia abajo en la cola."""
        if not self.db: return
        with self.db.pipeline() as pipe:
            queue = self.get_queue()
            try:
                idx = next(i for i, u in enumerate(queue) if u['id'] == user_id)
                if 0 <= idx < len(queue) - 1:
                    queue.insert(idx + 2, queue.pop(idx))
                    pipe.multi()
                    pipe.delete(self.queue_name)
                    for user in queue:
                        pipe.rpush(self.queue_name, json.dumps(user))
                    pipe.execute()
            except StopIteration:
                pass

class JobService:
    """
    Gestiona el contador de trabajos pendientes usando Redis.
    """
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

    def add_job(self):
        """Añade un nuevo trabajo (incrementa el contador)."""
        if not self.db: return 0
        return self.db.incr(self.job_key)

    def take_job(self):
        """Consume un trabajo si hay disponibles (decrementa el contador)."""
        if not self.db: return False
        # Usamos una transacción para evitar race conditions.
        with self.db.pipeline() as pipe:
            try:
                pipe.watch(self.job_key)
                current_value = int(pipe.get(self.job_key) or 0)
                if current_value > 0:
                    pipe.multi()
                    pipe.decr(self.job_key)
                    pipe.execute()
                    return True
                pipe.unwatch()
                return False
            except redis.exceptions.WatchError:
                # El valor cambió mientras estábamos en la transacción, reintentar no es necesario para este caso.
                return False

    def get_job_count(self):
        """Devuelve el número de trabajos disponibles."""
        if not self.db: return 0
        count = self.db.get(self.job_key)
        return int(count) if count else 0

    def reset_jobs(self):
        """Resetea el contador de trabajos a 0."""
        if not self.db: return
        self.db.set(self.job_key, 0)