# app/routes/auth_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import logout_user, login_user
from ..python.service import UserService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if UserService.validate_credentials(username, password):
            user = UserService.get_user_by_name(username)
            if user:
                login_user(user)
                
        
        flash('Usuario o contraseña incorrectos.')
        return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user() # Llama a la función importada
    return redirect(url_for('auth.login'))