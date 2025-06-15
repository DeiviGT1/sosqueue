import os
from dotenv import load_dotenv

# Carga las variables de entorno ANTES que cualquier otra cosa de la app
load_dotenv()

# Aplica el parche de gevent para que la red funcione correctamente
from gevent import monkey
monkey.patch_all()

# Ahora importa el resto de tu aplicación
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    socketio.run(app, host='0.0.0.0', port=port)