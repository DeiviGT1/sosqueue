from flask import Blueprint, render_template, request, jsonify
# Importamos los servicios Y el cliente de redis que creamos en service.py
from ..python.service import QueueService, JobService, redis_client 
from flask_login import login_required

sos_bp = Blueprint('sosqueue', __name__)

# --- CAMBIO CRÍTICO ---
# Creamos UNA SOLA instancia de cada servicio, PASANDO EL CLIENTE DE REDIS.
# Ahora estos servicios operarán sobre la base de datos, no sobre la memoria.
queue_service = QueueService(redis_client)
job_service = JobService(redis_client)

@sos_bp.route('/')
@login_required
def index():
    # Ahora, cuando se llamen estos métodos, obtendrán los datos desde Redis.
    available_users = queue_service.get_queue('sosq:available')
    working_users = queue_service.get_queue('sosq:working')
    idle_users = queue_service.get_queue('sosq:idle')
    job_count = job_service.get_job_count()
    
    # El template main.html no necesita cambios, ya que la estructura de datos es la misma.
    return render_template('main.html', 
                           available_users=available_users,
                           working_users=working_users,
                           idle_users=idle_users,
                           job_count=job_count)

# Las rutas de API que tenías antes ya no son necesarias si todo se maneja
# por WebSockets, pero las dejamos aquí por si las usas para algo más.
# Si no las usas, puedes eliminarlas para simplificar el código.

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
