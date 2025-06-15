# app/routes_main.py

from flask_bootstrap import Bootstrap
from .extensions import login_manager
# Importamos el servicio, que es seguro y no crea bucles
from .python.service import UserService

@login_manager.user_loader
def load_user(user_id):
    """Esta función es usada por Flask-Login para recargar el objeto de usuario."""
    return UserService.get_user_by_id(user_id)


def register_routes(app):
    """Inicializa extensiones y registra los blueprints en la aplicación."""
    Bootstrap(app)
    login_manager.init_app(app)

    # --- Registrar Blueprints ---
    from .routes.sosqueue_routes import sos_bp
    from .routes.auth_routes import auth_bp
    
    app.register_blueprint(sos_bp)
    app.register_blueprint(auth_bp)