import os
from flask import Flask

# Importa las instancias de las extensiones
from .extensions import socketio, login_manager
from .routes_main import register_routes
from .websockets import register_websockets


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    # Inicializa las extensiones con la app
    socketio.init_app(app)
    login_manager.init_app(app)

    # Registra las rutas y los websockets
    register_routes(app)
    register_websockets(socketio)
    
    print("Aplicación creada y configurada.")
    return app