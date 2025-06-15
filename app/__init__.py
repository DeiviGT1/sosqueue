# # app/__init__.py

# from flask import Flask
# # from flask_socketio import SocketIO
# from .routes_main import register_routes
# # import eventlet

# # eventlet.monkey_patch()

# # socketio = SocketIO(cors_allowed_origins="*")

# from flask import Flask
# from flask_login import LoginManager
# from flask_bootstrap import Bootstrap

# def create_app():
#     app = Flask(__name__)
#     app.config['SECRET_KEY'] = 'gunicorn'

#     # Initialize extensions
#     Bootstrap(app)
#     login_manager = LoginManager()
#     login_manager.login_view = 'auth.login'
#     login_manager.init_app(app)

#     return app



# # def create_app():
# #     app = Flask(__name__)

# #     # --- AÑADE ESTA RUTA DE PRUEBA AQUÍ ---
# #     @app.route('/test')
# #     def test_page():
# #         return "<h1>La app base funciona!</h1>"
# #     # -----------------------------------------

# #     app.config['SECRET_KEY'] = 'gunicorn' #

# #     from dotenv import load_dotenv
# #     load_dotenv()

# #     # socketio.init_app(app)
# #     # register_routes(app)
# #     return app

from flask import Flask
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'gunicorn'

    # Register the test blueprint
    from .routes.test import test
    app.register_blueprint(test)

    return app