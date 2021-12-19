from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import os
db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    if app.config['SSL_REDIRECT']:
        from flask_sslify import SSLify
        sslify = SSLify(app)
    flask_bcrypt = Bcrypt(app)
    jwt.init_app(app)
    # from .main import main as main_blueprint
    # app.register_blueprint(main_blueprint)

    # from .auth import auth as auth_blueprint
    # app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app
