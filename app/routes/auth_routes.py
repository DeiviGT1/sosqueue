# app/routes/auth_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import (
    login_user, logout_user, login_required,
    UserMixin, LoginManager
)

# ------------------------------------------------------------------
# Credenciales (usuario: {id, password, admin?})
# ------------------------------------------------------------------
_CREDENTIALS = {
    'admin':   {'id': 0, 'password': 'admin', 'admin': True},  # super-usuario
    'Juanfer': {'id': 1, 'password': '1'},
    'Edison':  {'id': 2, 'password': '2'},
    'Johan':  {'id': 3, 'password': '3'},
    'emp':     {'id': 4, 'password': '4'},
}

# ------------------------------------------------------------------
# Modelo de usuario para Flask-Login
# ------------------------------------------------------------------
class User(UserMixin):
    def __init__(self, user_id: int, username: str, is_admin: bool = False):
        self.id = user_id
        self.username = username
        self.is_admin = is_admin  # marca si es administrador

# ------------------------------------------------------------------
# Blueprint de autenticación + LoginManager
# ------------------------------------------------------------------
auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()          # se une a la app al registrar el BP


@auth_bp.record_once
def _setup_login(state):
    """Se ejecuta al registrar el blueprint: une LoginManager a la app."""
    login_manager.init_app(state.app)
    login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id: str):
    """
    Reconstruye el objeto User a partir del ID almacenado en sesión,
    preservando la bandera is_admin.
    """
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None

    for uname, cred in _CREDENTIALS.items():
        if cred['id'] == uid:
            return User(cred['id'], uname, cred.get('admin', False))
    return None


# ------------------------------------------------------------------
# Rutas de login / logout
# ------------------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form.get('username', '').strip()
        pwd   = request.form.get('password', '').strip()
        cred  = _CREDENTIALS.get(uname)

        if cred and pwd == cred['password']:
            user = User(cred['id'], uname, cred.get('admin', False))
            login_user(user)
            return redirect(url_for('sosqueue.index'))

        flash('Usuario o contraseña inválidos', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('sosqueue.index'))