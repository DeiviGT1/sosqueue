import os
from dotenv import load_dotenv

# Carga las variables de entorno ANTES que cualquier otra cosa de la app
load_dotenv()

# Ahora aplica el parche de gevent
from gevent import monkey
monkey.patch_all()

# Y ahora importa el resto de tu aplicación
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    socketio.run(app, host='0.0.0.0', port=port)