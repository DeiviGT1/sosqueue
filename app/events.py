from flask import request
from flask_login import current_user
from flask_socketio import emit
from . import socketio
from .routes.sosqueue_routes import queue_service, job_service

def get_full_state():
    """Combina el estado de las colas y los trabajos en un solo objeto."""
    state = queue_service.get_full_state()
    state['job_count'] = job_service.get_job_count()
    return state

@socketio.on('connect')
def handle_connect():
    """Cuando un cliente se conecta, le enviamos el estado actual."""
    print(f"Cliente conectado: {request.sid}")
    emit('update_state', get_full_state())

@socketio.on('set_available')
def handle_set_available():
    """Pone al usuario actual en la cola de disponibles."""
    if current_user.is_authenticated:
        queue_service.join_available(current_user)
        emit('update_state', get_full_state(), broadcast=True)

@socketio.on('add_job')
def handle_add_job():
    """Añade un nuevo trabajo y notifica a todos."""
    job_service.increment_job_count()
    emit('update_state', get_full_state(), broadcast=True)

@socketio.on('work')
def handle_work():
    """Mueve al primer usuario disponible a la cola de trabajo."""
    if current_user.is_authenticated:
        # Solo el primer usuario en la cola de disponibles puede empezar a trabajar
        available_users = queue_service.get_full_state()['available_users']
        if available_users and available_users[0]['id'] == current_user.id:
            if job_service.get_job_count() > 0:
                if queue_service.move_to_working(current_user.id):
                    job_service.decrement_job_count()
                    emit('update_state', get_full_state(), broadcast=True)

@socketio.on('finish')
def handle_finish():
    """Mueve a un usuario de 'trabajando' a 'disponible'."""
    if current_user.is_authenticated:
        queue_service.move_to_available(current_user.id)
        emit('update_state', get_full_state(), broadcast=True)

@socketio.on('idle')
def handle_idle():
    """Mueve al usuario actual a la cola de descanso."""
    if current_user.is_authenticated:
        queue_service.move_to_idle(current_user.id)
        emit('update_state', get_full_state(), broadcast=True)

# --- Eventos para Administradores ---

@socketio.on('set_idle')
def handle_set_idle(data):
    """(Admin) Mueve a un usuario específico a descanso."""
    if current_user.is_authenticated and current_user.is_admin:
        user_id = int(data['user_id'])
        queue_service.move_to_idle(user_id)
        emit('update_state', get_full_state(), broadcast=True)