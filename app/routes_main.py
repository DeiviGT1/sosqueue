# app/routes_main.py

from flask_login import LoginManager
from flask_bootstrap import Bootstrap

login_manager = LoginManager()
# El nombre de la ruta ahora es 'auth.login' (blueprint.funcion)
login_manager.login_view = 'auth.login'

def register_routes(app):
    # --- Inicializar extensiones ---
    Bootstrap(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # --- user_loader para reconstruir al usuario desde su ID ---
    from .routes.auth_routes import User, _CREDENTIALS
    @login_manager.user_loader
    def load_user(user_id):
        for username, cred in _CREDENTIALS.items():
            if cred['id'] == int(user_id):
                return User(cred['id'], username, cred.get('admin', False))
        return None

    # --- Registrar blueprints (sin cambios) ---
    from .routes.sosqueue_routes import sos_bp
    from .routes.auth_routes import auth_bp
    app.register_blueprint(sos_bp)
    app.register_blueprint(auth_bp)