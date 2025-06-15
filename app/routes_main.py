# Importa el login_manager desde extensions
from .extensions import login_manager
from .routes.sosqueue_routes import sos_bp
from .routes.auth_routes import auth_bp
from .python.service import UserService

@login_manager.user_loader
def load_user(user_id):
    return UserService.get(user_id)

def register_routes(app):
    app.register_blueprint(sos_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')