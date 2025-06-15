# # app/websockets.py

# from flask_socketio import SocketIO, emit

# # Se crea la instancia de SocketIO
# socketio = SocketIO()

# def init_app(app):
#     """Inicializa SocketIO con la aplicación Flask."""
#     socketio.init_app(app, cors_allowed_origins="*")

# @socketio.on('connect')
# def handle_connect():
#     """
#     Este evento se dispara cuando un cliente se conecta.
#     Opcionalmente, puedes emitir un mensaje de bienvenida.
#     """
#     print('Client connected')
#     emit('status', {'message': 'Conectado al servidor!'})

# @socketio.on('disconnect')
# def handle_disconnect():
#     """
#     Este evento se dispara cuando un cliente se desconecta.
#     """
#     print('Client disconnected')