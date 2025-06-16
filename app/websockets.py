# app/websockets.py

from flask import request 
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
        get_and_emit_full_state(sid=request.sid)

    @socketio.on('disconnect')
    def handle_disconnect():
        """Cliente desconectado."""
        print('Client disconnected', flush=True)

    @socketio.on('add_job')
    def handle_add_job():
        """
        Manejador para el evento 'add_job'.
        Simplemente incrementa el contador de trabajos.
        """
        logging.info("[SERVIDOR] Evento 'add_job' recibido.")
        
        if not current_user.is_admin:
            return
            
        job_service.increment_job_count()
        logging.info(f"Job count incremented to: {job_service.get_job_count()}")
        
        get_and_emit_full_state()

    # --- 👇 AÑADE ESTAS TRES NUEVAS FUNCIONES AQUÍ 👇 ---

    @socketio.on('set_available')
    def handle_set_available():
        """
        Manejador para cuando un usuario se pone en estado 'disponible'.
        Usa el método correcto: join_available.
        """
        if not current_user.is_authenticated or current_user.is_admin:
            return

        logging.info(f"[SERVIDOR] Evento 'set_available' recibido del usuario: {current_user.name}")
        # CORRECCIÓN: El método se llama 'join_available' en service.py
        queue_service.join_available(current_user) 
        get_and_emit_full_state()

    @socketio.on('set_idle')
    def handle_set_idle():
        """
        Manejador para cuando un usuario se pone en estado 'ocupado' (idle).
        """
        if not current_user.is_authenticated or current_user.is_admin:
            return

        logging.info(f"[SERVIDOR] Evento 'set_idle' recibido del usuario: {current_user.name}")
        # CORRECCIÓN: El método se llama 'move_to_idle' y espera un ID
        queue_service.move_to_idle(current_user.id)
        get_and_emit_full_state()

    @socketio.on('set_working')
    def handle_set_working():
        """
        Manejador para cuando un usuario se pone en estado 'trabajando'.
        """
        if not current_user.is_authenticated or current_user.is_admin:
            return
            
        logging.info(f"[SERVIDOR] Evento 'set_working' recibido del usuario: {current_user.name}")
        # CORRECCIÓN: El método se llama 'move_to_working' y espera un ID
        queue_service.move_to_working(current_user.id)
        get_and_emit_full_state()

    def get_and_emit_full_state(sid=None):
        """
        Función auxiliar para obtener el estado completo y emitirlo.
        """
        state = queue_service.get_full_state()
        state['job_count'] = job_service.get_job_count()
        
        target_room = sid if sid else None
        broadcast = not bool(target_room)
        
        logging.info(f"[SERVIDOR] Enviando 'update_state' con datos: {state}")
        emit('update_state', state, to=target_room, broadcast=broadcast)