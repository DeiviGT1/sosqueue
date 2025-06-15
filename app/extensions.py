from flask_socketio import SocketIO
from flask_login import LoginManager

# Declaramos las extensiones aquí, sin inicializarlas con la app
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')
login_manager = LoginManager()
login_manager.login_view = 'auth.login'