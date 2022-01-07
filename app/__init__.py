from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import os
import redis
db = SQLAlchemy()
jwt = JWTManager()
pool0 = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True,db=0)
pool1 = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True,db=1)
rdb0 = redis.Redis(connection_pool=pool0) # redis db 0  保存人脸特征
rdb1 = redis.Redis(connection_pool=pool1) # redis db 1 保存 推荐人列表,最多10个


def create_app(config_name):
    app = Flask(__name__)
    app.logger.debug(config_name)
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
