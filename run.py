import os
from dotenv import load_dotenv

# Carga las variables de entorno ANTES que cualquier otra cosa de la app
load_dotenv()

# Ahora importa el resto de tu aplicación
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run()