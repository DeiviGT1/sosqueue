# app/events.py

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
def handle_set_available(data=None): # <-- CAMBIO AQUÍ
    """Pone al usuario actual en la cola de disponibles."""
    if current_user.is_authenticated:
        queue_service.join_available(current_user)
        emit('update_state', get_full_state(), broadcast=True)

@socketio.on('add_job')
def handle_add_job(data=None): # <-- CAMBIO AQUÍ
    """Añade un nuevo trabajo y notifica a todos."""
    job_service.increment_job_count()
    emit('update_state', get_full_state(), broadcast=True)

@socketio.on('work')
def handle_work(data=None): # <-- CAMBIO AQUÍ
    """Mueve al primer usuario disponible a la cola de trabajo."""
    if current_user.is_authenticated:
        available_users = queue_service.get_full_state()['available_users']
        if available_users and available_users[0]['id'] == current_user.id:
            if job_service.get_job_count() > 0:
                if queue_service.move_to_working(current_user.id):
                    job_service.decrement_job_count()
                    emit('update_state', get_full_state(), broadcast=True)

@socketio.on('finish')
def handle_finish(data=None): # <-- CAMBIO AQUÍ
    """Mueve a un usuario de 'trabajando' a 'disponible'."""
    if current_user.is_authenticated:
        queue_service.move_to_available(current_user.id)
        emit('update_state', get_full_state(), broadcast=True)

@socketio.on('idle')
def handle_idle(data=None): # <-- CAMBIO PRINCIPAL AQUÍ
    """Mueve al usuario actual a la cola de descanso."""
    if current_user.is_authenticated:
        queue_service.move_to_idle(current_user.id)
        emit('update_state', get_full_state(), broadcast=True)

# --- Eventos para Administradores ---
# NOTA: Estas funciones ya esperan datos, así que estaban correctas.
# Asegúrate de que tu frontend envíe los datos como un diccionario.
# Ejemplo: socket.emit('set_idle', {'user_id': 3});

@socketio.on('set_idle')
def handle_set_idle(data=None):
    """(Admin) Mueve a un usuario específico a descanso."""
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        user_id = int(data['user_id'])
        queue_service.move_to_idle(user_id)
        emit('update_state', get_full_state(), broadcast=True)

# --- Aquí puedes añadir los nuevos eventos para subir/bajar empleados ---

@socketio.on('move_up')
def handle_move_up(data):
    """(Admin) Mueve un usuario hacia arriba en la cola."""
    if current_user.is_authenticated and current_user.is_admin:
        try:
            user_id = int(data['user_id'])
            queue_service.move_user_up(user_id)
            emit('update_state', get_full_state(), broadcast=True)
        except (KeyError, TypeError):
            print("Error: 'user_id' no fue proporcionado en el evento 'move_up'.")


@socketio.on('move_down')
def handle_move_down(data):
    """(Admin) Mueve un usuario hacia abajo en la cola."""
    if current_user.is_authenticated and current_user.is_admin:
        try:
            user_id = int(data['user_id'])
            queue_service.move_user_down(user_id)
            emit('update_state', get_full_state(), broadcast=True)
        except (KeyError, TypeError):
            print("Error: 'user_id' no fue proporcionado en el evento 'move_down'.")

@socketio.on('remove_job')
def handle_remove_job(data=None):
    """(Admin) Disminuye el contador de trabajos en uno."""
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        job_service.decrement_job_count()
        emit('update_state', get_full_state(), broadcast=True)