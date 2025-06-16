from flask_login import current_user
from flask_socketio import emit
from .extensions import socketio
from .python.service import QueueService
from .python.service import JobService
import logging


queue_service = QueueService()
job_service = JobService()
def register_websockets(socketio):
    @socketio.on('connect')
    def handle_connect(auth):
        """Cliente conectado."""
        print('Client connected', flush=True)
        emit('update_state', queue_service.get_full_state())
            
    @socketio.on('disconnect')
    def handle_disconnect():
        """Cliente desconectado."""
        print('Client disconnected', flush=True)
        emit('update_state', queue_service.get_full_state())

    @socketio.on('add_job')
    def handle_add_job():
        """
        Manejador para el evento 'add_job'.
        Simplemente incrementa el contador de trabajos.
        """
        # LOG DE VERIFICACIÓN: Confirma que el servidor recibe el evento.
        logging.info("[SERVIDOR] Evento 'add_job' recibido.")
        
        if not current_user.is_admin:
            return
            
        job_service.increment_job_count()
        logging.info(f"Job count incremented to: {job_service.get_job_count()}")
        
        # Llama a la función auxiliar que ahora construye el estado correctamente
        get_and_emit_full_state()

    def get_and_emit_full_state(sid=None):
        """
        Función auxiliar para obtener el estado completo y emitirlo.
        """
        # 1. Obtiene el estado de las colas de usuarios
        state = queue_service.get_full_state()
        # 2. Obtiene el contador de trabajos y lo AÑADE al estado
        state['job_count'] = job_service.get_job_count()
        
        target_room = sid if sid else None
        broadcast = not bool(target_room)
        
        logging.info(f"[SERVIDOR] Enviando 'update_state' con datos: {state}")
        emit('update_state', state, to=target_room, broadcast=broadcast)