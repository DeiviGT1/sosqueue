# app/models.py

from flask_login import UserMixin

class User(UserMixin):
    """
    Clase que representa un usuario en el sistema.
    Hereda de UserMixin para obtener las propiedades que Flask-Login necesita.
    """
    def __init__(self, id, name, pin, is_admin=False):
        self.id = id
        self.name = name
        self.pin = pin
        self.is_admin = is_admin

    def __repr__(self):
        return f'<User: {self.name}>'