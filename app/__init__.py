import os
from flask import Flask
from uuid import uuid4

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.secret_key = uuid4().hex  # セッション用の秘密鍵

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app

