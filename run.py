import os
from dotenv import load_dotenv

# Carga las variables de entorno
load_dotenv()

# Importa la app y la instancia de socketio
from app import create_app, socketio

# Flask app para desarrollo local
flask_app = create_app()

# WSGI app para plataformas como Vercel (expone 'app' como callable)
app = socketio.WSGIApp(socketio, flask_app)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    # Ejecución local (sin logs de depuración adicionales)
    socketio.run(flask_app, host='0.0.0.0', port=port, debug=False)