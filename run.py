# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Ejecuta la aplicación en modo debug para desarrollo
    app.run(host='127.0.0.1', port=5001, debug=True)