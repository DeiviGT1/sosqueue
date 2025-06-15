from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from ..python.service import QueueService, JobService, UserService
from ..extensions import socketio

sos_bp = Blueprint('sosqueue', __name__)

# Creamos UNA SOLA instancia de cada servicio.
queue_service = QueueService()
job_service = JobService()
user_service = UserService()


@sos_bp.route('/')
@login_required
def index():
    # Usamos los nuevos métodos específicos del servicio
    available_users = queue_service.get_available_users()
    working_users = queue_service.get_working_users()
    idle_users = queue_service.get_idle_users()
    
    job_count = job_service.get_job_count()
    
    # Obtenemos los nombres de usuario para mostrar en la plantilla
    available_users_names = [user_service.get(uid).name for uid in available_users]
    working_users_names = [user_service.get(uid).name for uid in working_users]
    idle_users_names = [user_service.get(uid).name for uid in idle_users]
    
    return render_template('main.html', 
                           available_users=available_users_names,
                           working_users=working_users_names,
                           idle_users=idle_users_names,
                           job_count=job_count)


@sos_bp.route('/move_to_working', methods=['POST'])
@login_required
def move_to_working():
    user_id = request.form['user_id']
    queue_service.move_user_to_working(user_id)
    socketio.emit('update_queues', namespace='/')
    return jsonify(success=True)


@sos_bp.route('/move_to_idle', methods=['POST'])
@login_required
def move_to_idle():
    user_id = request.form['user_id']
    queue_service.move_user_to_idle(user_id)
    socketio.emit('update_queues', namespace='/')
    return jsonify(success=True)


@sos_bp.route('/move_to_available', methods=['POST'])
@login_required
def move_to_available():
    user_id = request.form['user_id']
    queue_name = request.form['queue_name']
    queue_service.move_user_to_available(user_id, queue_name)
    socketio.emit('update_queues', namespace='/')
    return jsonify(success=True)