from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

# IMPORT ROUTES
from routes.auth import auth_bp
from routes.ideas import ideas_bp
from routes.profile import profile_bp
from routes.session import session_bp

# SOCKET EVENTS
import socket_events

# APP CONFIG
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

socketio = SocketIO(app)

# REGISTER BLUEPRINTS
app.register_blueprint(auth_bp)
app.register_blueprint(ideas_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(session_bp)

# SOCKET INIT EVENTS
socket_events.init_socket(socketio)

if __name__ == "__main__":
    socketio.run(app, debug=True)
