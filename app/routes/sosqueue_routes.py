# app/routes/sosqueue_routes.py

from flask import Blueprint, render_template, jsonify, abort, request
from flask_login import login_required, current_user
# Se importan los servicios actualizados que usan Redis
from app.python.service import QueueService, JobService
import os

sos_bp = Blueprint('sosqueue', __name__, url_prefix='/')

# Se instancian los servicios con nombres de clave únicos para Redis
available_queue = QueueService('sosq:available')
working_queue = QueueService('sosq:working')
idle_queue = QueueService('sosq:idle')
job_queue = JobService()

def _require_admin():
    if not getattr(current_user, 'is_admin', False):
        abort(403)

# --- Lógica del Scheduler (para Vercel Cron Jobs) ---
def reset_all_queues():
    print("SCHEDULER: Ejecutando reseteo diario de colas...")
    working_queue.move_all_to(idle_queue)
    available_queue.move_all_to(idle_queue)
    print("SCHEDULER: Reseteo completado.")
    
# --- NUEVA FUNCIÓN AUXILIAR PARA OBTENER EL ESTADO ---
def _get_current_state():
    """
    Función centralizada que obtiene el estado completo desde Redis.
    Devuelve un diccionario con toda la información de las colas.
    """
    available_users = available_queue.get_queue()
    working_users = working_queue.get_queue()
    idle_users = idle_queue.get_queue()
    job_count = job_queue.get_job_count()
    active_ids = {u['id'] for u in available_users} | {u['id'] for u in working_users}

    return {
        'available_users': available_users,
        'working_users': working_users,
        'idle_users': idle_users,
        'job_count': job_count,
        'active_ids': list(active_ids),
    }

# --- RUTAS ACTUALIZADAS ---

@sos_bp.route('/')
@login_required
def index():
    """
    CAMBIO: Ahora obtiene el estado inicial del backend y lo pasa a la plantilla.
    Esto permite que la página se renderice con los datos correctos desde el primer momento.
    """
    initial_state = _get_current_state()
    # Usamos ** para desempaquetar el diccionario como argumentos para la plantilla.
    # Esto es equivalente a: render_template('...', available_users=initial_state['available_users'], etc.)
    return render_template('main.html', **initial_state)

@sos_bp.route('/state', methods=['GET'])
@login_required
def get_state():
    """
    CAMBIO: Ahora simplemente llama a la función auxiliar para obtener el estado.
    Esta ruta es la que usa el JavaScript para las actualizaciones periódicas.
    """
    return jsonify(_get_current_state())

# --- El resto de las rutas (Acciones de Empleados y Admin) permanecen exactamente igual ---

@sos_bp.route('/available', methods=['POST'])
@login_required
def become_available():
    if current_user.is_admin:
        return jsonify({'error': 'Los administradores no entran en la cola'}), 403
    idle_queue.remove(current_user.id)
    available_queue.join(current_user)
    return jsonify({'status': 'ok'})

@sos_bp.route('/work', methods=['POST'])
@login_required
def start_work():
    available_users = available_queue.get_queue()
    if not available_users or available_users[0]['id'] != current_user.id:
        return jsonify({'error': 'No es tu turno para tomar un trabajo.'}), 403

    if job_queue.take_job():
        user_dict = available_queue.pop_first()
        if user_dict:
            temp_user = type('User', (object,), {'id': user_dict['id'], 'username': user_dict['name']})
            working_queue.join(temp_user)
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'error': 'No hay trabajos disponibles en este momento.'}), 400

@sos_bp.route('/finish', methods=['POST'])
@login_required
def finish_work():
    if working_queue.remove(current_user.id):
        available_queue.join(current_user)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'No estabas en la lista de trabajo.'}), 404

@sos_bp.route('/idle', methods=['POST'])
@login_required
def become_idle():
    if available_queue.remove(current_user.id):
        idle_queue.join(current_user)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'No estabas en la cola de disponibles.'}), 404

@sos_bp.route('/admin/add_job', methods=['POST'])
@login_required
def admin_add_job():
    _require_admin()
    job_queue.add_job()
    return jsonify({'status': 'ok', 'new_count': job_queue.get_job_count()})

@sos_bp.route('/admin/move/<int:user_id>/<string:direction>', methods=['POST'])
@login_required
def admin_move(user_id, direction):
    _require_admin()
    if direction == 'up':
        available_queue.move_up(user_id)
    elif direction == 'down':
        available_queue.move_down(user_id)
    return jsonify({'status': 'ok'})

@sos_bp.route('/admin/set_idle/<int:user_id>', methods=['POST'])
@login_required
def admin_set_idle(user_id):
    _require_admin()
    all_users = available_queue.get_queue() + working_queue.get_queue()
    user_data = next((u for u in all_users if u['id'] == user_id), None)
    
    if not user_data:
        return jsonify({'error': 'Usuario no encontrado en colas activas'}), 404

    available_queue.remove(user_id)
    working_queue.remove(user_id)
    
    temp_user = type('User', (object,), {'id': user_data['id'], 'username': user_data['name']})
    idle_queue.join(temp_user)
    
    return jsonify({'status': 'ok'})

@sos_bp.route('/api/reset-queues', methods=['POST'])
def reset_queues_api():
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {os.environ.get('CRON_SECRET')}":
        return jsonify({'error': 'Unauthorized'}), 401
    reset_all_queues()
    return jsonify({'status': 'ok'})