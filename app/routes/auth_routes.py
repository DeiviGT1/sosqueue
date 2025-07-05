# app/routes/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..python.service import UserService
from ..models.User import User # Asegúrate que la ruta de importación es correcta

# Crea un Blueprint. Un Blueprint es una forma de organizar un grupo de rutas relacionadas.
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validamos credenciales usando nuestro servicio
        if UserService.validate_credentials(username, password):
            user = UserService.get_user_by_name(username)
            if user:
                login_user(user)
                flash('Inicio de sesión exitoso.', 'success')
                # Redirige al usuario a la cola después de iniciar sesión
                return redirect(url_for('sosqueue.index'))
        
        flash('Nombre de usuario o contraseña incorrectos.', 'danger')

    # Si ya está autenticado, lo mandamos a la cola directamente
    if current_user.is_authenticated:
        return redirect(url_for('sosqueue.index'))

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('auth.login'))