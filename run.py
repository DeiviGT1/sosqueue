import eventlet
eventlet.monkey_patch() # <-- AÑADIR ESTA LÍNEA

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # Esta línea ahora usará el servidor de eventlet gracias al monkey patch
    socketio.run(app, debug=True)