import os
from dotenv import load_dotenv

# Carga las variables de entorno
load_dotenv()

# Importa la app y la instancia de socketio
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    # Usa socketio.run() en lugar de app.run()
    # El host '0.0.0.0' permite acceder desde otros dispositivos en la misma red
    socketio.run(app, host='0.0.0.0', port=port, debug=True)