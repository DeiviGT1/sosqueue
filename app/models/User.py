from flask_login import UserMixin

class User(UserMixin):
    """
    Clase que representa un usuario en el sistema.
    Hereda de UserMixin para obtener las propiedades que Flask-Login necesita
    (is_authenticated, is_active, is_anonymous, get_id).
    """
    def __init__(self, id, name, pin):
        self.id = id
        self.name = name
        self.pin = pin

    def __repr__(self):
        return f'<User: {self.name}>'