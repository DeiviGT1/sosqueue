# app/__init__.py

import os
from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager
from .python.service import UserService # Asegúrate que la ruta de importación es correcta
from .models.User import User # Asegúrate que la ruta de importación es correcta

# Crea las instancias de SocketIO y LoginManager aquí
# Permite forzar el modo async por variable de entorno (producción sin logs de debug)
ASYNC_MODE = os.environ.get("SIO_ASYNC_MODE", "threading")  # opciones: 'eventlet', 'gevent', 'threading'
socketio = SocketIO(cors_allowed_origins="*", async_mode=ASYNC_MODE)
login_manager = LoginManager()
# Esta línea le dice a Flask-Login a qué vista redirigir si un usuario no autenticado intenta acceder a una página protegida.
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    """
    Esta función es requerida por Flask-Login para cargar un usuario
    a partir del ID almacenado en la sesión.
    """
    return UserService.get_user_by_id(int(user_id))


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una-clave-secreta-muy-segura')


    # Inicializa los componentes con la app (con CORS explícito para Socket.IO)
    socketio.init_app(app, cors_allowed_origins="*")
    login_manager.init_app(app)









    # Importa y registra los Blueprints (rutas)
    from .routes.auth_routes import auth_bp
    from .routes.sosqueue_routes import sos_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(sos_bp)

    # Importa los eventos de WebSocket
    from . import events

    return app