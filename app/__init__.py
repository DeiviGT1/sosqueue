import os
from flask import Flask
from flask_socketio import SocketIO

# Crea la instancia de SocketIO aquí, pero no la inicialices todavía
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una-clave-secreta-muy-segura')

    # Importa los servicios y rutas DESPUÉS de crear la app para evitar importaciones circulares
    from .routes_main import register_routes
    from . import events  # Importa los eventos de WebSocket

    # Registra las rutas y los blueprints
    register_routes(app)

    # Inicializa SocketIO con la app
    socketio.init_app(app)

    print("Aplicación creada y configurada con WebSockets.")
    return app