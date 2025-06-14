from flask import Flask
from flask_socketio import SocketIO
from .routes_main import register_routes

# Inicializa SocketIO aquí, permitiendo todas las conexiones de origen
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'

    from dotenv import load_dotenv
    load_dotenv()

    # Inicializa SocketIO con la configuración de la app
    socketio.init_app(app)

    # Registra las rutas
    register_routes(app)

    return app