from flask_login import current_user
# Cambia esta línea: from app import socketio
from .extensions import socketio # <- Por esta
from .python.service import QueueService

queue_service = QueueService()

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