from flask_login import current_user
from flask_socketio import emit
from .extensions import socketio # <- Por esta
from .python.service import QueueService
from .python.service import JobService


queue_service = QueueService()
job_service = JobService()
def register_websockets(socketio_instance):
    
    @socketio_instance.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            queue_service.add_user_to_available(current_user)
            socketio_instance.emit('update_queues')
            print(f'Client connected: {current_user.name}')
            
    @socketio_instance.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            queue_service.remove_user_from_all_queues(current_user.id)
            socketio_instance.emit('update_queues')
            print(f'Client disconnected: {current_user.name}')

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
        emit('update_queue', job_service.get_queue_status(), broadcast=True)