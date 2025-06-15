# # app/routes/sosqueue_routes.py

# from flask import Blueprint, render_template, jsonify, abort, request
# from flask_login import login_required, current_user
# from app.python.service import QueueService, JobService
# from app import socketio # <-- 1. Importar socketio
# import os

# sos_bp = Blueprint('sosqueue', __name__, url_prefix='/')

# # (Las instancias de los servicios permanecen igual)
# available_queue = QueueService('sosq:available')
# working_queue = QueueService('sosq:working')
# idle_queue = QueueService('sosq:idle')
# job_queue = JobService()

# @socketio.on('connect')
# def handle_connect():
#     """
#     Esta función se ejecuta cuando un cliente se conecta vía WebSocket.
#     Nos sirve para confirmar que la conexión funciona.
#     """
#     print('✅ Cliente conectado via WebSocket!')

# def _require_admin():
#     if not getattr(current_user, 'is_admin', False):
#         abort(403)

# # --- NUEVA FUNCIÓN AUXILIAR PARA OBTENER Y EMITIR EL ESTADO ---
# def _get_and_emit_state():
#     """
#     Obtiene el estado completo y lo emite a todos los clientes
#     a través de un evento WebSocket llamado 'update_state'.
#     """
#     state = {
#         'available_users': available_queue.get_queue(),
#         'working_users': working_queue.get_queue(),
#         'idle_users': idle_queue.get_queue(),
#         'job_count': job_queue.get_job_count(),
#     }
#     # Emite el evento a todos los clientes conectados
#     socketio.emit('update_state', state)
#     return state

# # --- RUTAS ACTUALIZADAS ---

# @sos_bp.route('/')
# @login_required
# def index():
#     """
#     Renderiza la página inicial con el estado actual.
#     El estado se obtiene directamente, sin la función de emisión.
#     """
#     initial_state = {
#         'available_users': available_queue.get_queue(),
#         'working_users': working_queue.get_queue(),
#         'idle_users': idle_queue.get_queue(),
#         'job_count': job_queue.get_job_count(),
#         'active_ids': list({u['id'] for u in available_queue.get_queue()} | {u['id'] for u in working_queue.get_queue()})
#     }
#     return render_template('main.html', **initial_state)


# @sos_bp.route('/available', methods=['POST'])
# @login_required
# def become_available():
#     if current_user.is_admin:
#         return jsonify({'error': 'Los administradores no entran en la cola'}), 403
#     idle_queue.remove(current_user.id)
#     available_queue.join(current_user)
#     _get_and_emit_state() # <-- Emitir cambios
#     return jsonify({'status': 'ok'})

# @sos_bp.route('/work', methods=['POST'])
# @login_required
# def start_work():
#     available_users = available_queue.get_queue()
#     if not available_users or available_users[0]['id'] != current_user.id:
#         return jsonify({'error': 'No es tu turno para tomar un trabajo.'}), 403

#     if job_queue.take_job():
#         user_dict = available_queue.pop_first()
#         if user_dict:
#             temp_user = type('User', (object,), {'id': user_dict['id'], 'username': user_dict['name']})
#             working_queue.join(temp_user)
#         _get_and_emit_state() # <-- Emitir cambios
#         return jsonify({'status': 'ok'})
#     else:
#         return jsonify({'error': 'No hay trabajos disponibles en este momento.'}), 400

# # ... (Aplica el mismo cambio a todas las demás rutas de acción) ...

# @sos_bp.route('/finish', methods=['POST'])
# @login_required
# def finish_work():
#     if working_queue.remove(current_user.id):
#         available_queue.join(current_user)
#         _get_and_emit_state() # <-- Emitir cambios
#         return jsonify({'status': 'ok'})
#     return jsonify({'error': 'No estabas en la lista de trabajo.'}), 404

# @sos_bp.route('/idle', methods=['POST'])
# @login_required
# def become_idle():
#     if available_queue.remove(current_user.id):
#         idle_queue.join(current_user)
#         _get_and_emit_state() # <-- Emitir cambios
#         return jsonify({'status': 'ok'})
#     return jsonify({'error': 'No estabas en la cola de disponibles.'}), 404

# @sos_bp.route('/admin/add_job', methods=['POST'])
# @login_required
# def admin_add_job():
#     _require_admin()
#     job_queue.add_job()
#     _get_and_emit_state() # <-- Emitir cambios
#     return jsonify({'status': 'ok'})

# @sos_bp.route('/admin/move/<int:user_id>/<string:direction>', methods=['POST'])
# @login_required
# def admin_move(user_id, direction):
#     _require_admin()
#     if direction == 'up':
#         available_queue.move_up(user_id)
#     elif direction == 'down':
#         available_queue.move_down(user_id)
#     _get_and_emit_state() # <-- Emitir cambios
#     return jsonify({'status': 'ok'})

# @sos_bp.route('/admin/set_idle/<int:user_id>', methods=['POST'])
# @login_required
# def admin_set_idle(user_id):
#     _require_admin()
#     all_users = available_queue.get_queue() + working_queue.get_queue()
#     user_data = next((u for u in all_users if u['id'] == user_id), None)
    
#     if not user_data:
#         return jsonify({'error': 'Usuario no encontrado en colas activas'}), 404

#     available_queue.remove(user_id)
#     working_queue.remove(user_id)
    
#     temp_user = type('User', (object,), {'id': user_data['id'], 'username': user_data['name']})
#     idle_queue.join(temp_user)
    
#     _get_and_emit_state() # <-- Emitir cambios
#     return jsonify({'status': 'ok'})