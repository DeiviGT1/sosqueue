from flask import Blueprint, render_template, request, jsonify
from ..python.service import QueueService, JobService

sos_bp = Blueprint('sosqueue', __name__)

# Creamos UNA SOLA instancia de cada servicio, sin argumentos.
queue_service = QueueService()
job_service = JobService()

@sos_bp.route('/')
def index():
    # Usamos el servicio único para obtener cada cola
    available_users = queue_service.get_queue('sosq:available')
    working_users = queue_service.get_queue('sosq:working')
    idle_users = queue_service.get_queue('sosq:idle')
    job_count = job_service.get_job_count()
    
    return render_template('main.html', 
                           available_users=available_users,
                           working_users=working_users,
                           idle_users=idle_users,
                           job_count=job_count)


@sos_bp.route('/move_to_working', methods=['POST'])
def move_to_working():
    user_id = int(request.form['user_id'])
    queue_service.move_to_working(user_id)

    return jsonify(success=True)


@sos_bp.route('/move_to_idle', methods=['POST'])
def move_to_idle():
    user_id = int(request.form['user_id'])
    queue_service.move_to_idle(user_id)
    
    return jsonify(success=True)


@sos_bp.route('/move_to_available', methods=['POST'])
def move_to_available():
    user_id = int(request.form['user_id'])
    queue_service.move_to_available(user_id)

    return jsonify(success=True)