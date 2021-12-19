from flask import jsonify, request, current_app, url_for, g
from . import api
from ..models import User
from ..import db
import jwt
from flask_login import login_user, logout_user, login_required, \
    current_user
import json
from flask_jwt_extended import *
from flask_cors import CORS, cross_origin


@api.route('/register', methods=["POST"])  # 获取用户信息
@cross_origin()
def register_user():
    user = User.from_json(request.json)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_json()), 201, \
        {'Location': url_for('api.login', id=user.id)}


@api.route('/login', methods=["POST"])
@cross_origin()
def login_user():
    data = request.json
    username = data['username']
    password = data['password_hash']
    user = User.query.filter_by(username=username).first()
    if user is not None:
        if user.password_hash == password:
            token = create_access_token(identity=user.id)
            message = "login success"
        else:
            message = "password wrong"
    else:
        message = "user not exist"
    g.current_user = user
    test = user.to_json()
    test1 = jsonify(test)
    return jsonify({
        "current_user": user.to_json(),
        "message": message,
        "token": token
    })
