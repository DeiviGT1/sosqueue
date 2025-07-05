# app/routes_main.py

from flask_bootstrap import Bootstrap
# Importamos el servicio, que es seguro y no crea bucles
from .python.service import UserService


def register_routes(app):
    """Inicializa extensiones y registra los blueprints en la aplicación."""
    Bootstrap(app)

    # --- Registrar Blueprints ---
    from .routes.sosqueue_routes import sos_bp
    from .routes.auth_routes import auth_bp
    
    app.register_blueprint(sos_bp)
    app.register_blueprint(auth_bp)