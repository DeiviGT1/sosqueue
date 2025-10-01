import os
from dotenv import load_dotenv

# Carga las variables de entorno
load_dotenv()

# Importa la app y la instancia de socketio
from app import create_app, socketio

# WSGI callable para Vercel: expone directamente la app Flask
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    # Ejecución local (sin logs de depuración adicionales)
    socketio.run(app, host='0.0.0.0', port=port, debug=False)