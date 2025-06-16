from flask_login import current_user
from flask_socketio import emit
from .extensions import socketio
from .python.service import QueueService
from .python.service import JobService


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
    def handle_add_job(data):
        """
        Manejador para el evento 'add_job'.
        Añade un nuevo trabajo a la cola.
        """
        # --- INICIO DE LA CORRECCIÓN ---
        description = data.get('description', 'Sin descripción')
        job_service.add_job(description)
        print(f"Nuevo trabajo añadido: {description}")
        # --- FIN DE LA CORRECCIÓN ---
        
        # Notificar a todos los clientes sobre el cambio en la cola 
        emit('update_queue', job_service.get_job_count(), broadcast=True)