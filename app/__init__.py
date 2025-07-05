import os
from flask import Flask

# Importa las instancias de las extensiones
from .routes_main import register_routes


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    # Registra las rutas y los websockets
    register_routes(app)
    
    print("Aplicación creada y configurada.")
    return app