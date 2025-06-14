# app/__init__.py
from flask import Flask
from .routes_main import register_routes

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'

    from dotenv import load_dotenv
    load_dotenv()

    # Registrar las rutas
    register_routes(app)

    return app