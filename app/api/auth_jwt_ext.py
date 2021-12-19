from flask import request, jsonify
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                jwt_required, get_jwt, get_jwt_identity)
from . import api
from ..models import User, TokenBlocklist
from .. import db, jwt
from datetime import datetime, timedelta, timezone


@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({
        'ok': False,
        'message': 'Missing Authorization Header'
    }), 401


@jwt.invalid_token_loader
def invalid_token_response(callback):
    return jsonify({
        'ok': False,
        'message': 'Invalid Token'
    }), 401


@jwt.expired_token_loader
def expired_token_response(callback):
    return jsonify({
        'ok': False,
        'message': 'Expired Token'
    }), 401


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
    return token is not None


@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({
            'ok': False,
            'message': 'No input data provided'
        }), 400
    username = data.get('username')
    password = data.get('password')
    if not username:
        return jsonify({
            'ok': False,
            'message': 'No username provided'
        }), 400
    if not password:
        return jsonify({
            'ok': False,
            'message': 'No password provided'
        }), 400
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({
            'ok': False,
            'message': 'User already exists'
        }), 400
    user = User(username=username)
    user.password = password
    db.session.add(user)
    db.session.commit()
    return jsonify({
        'ok': True,
        'message': 'User registered successfully'
    }), 201


@api.route('/auth/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username:
        return jsonify({"msg": "Missing username parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "Bad username or password"}), 401
    if user.verify_password(password):
        access_token = create_access_token(identity=user.id, fresh=True)
        refresh_token = create_refresh_token(user.id)
        return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401


@api.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user, fresh=False)
    return jsonify({"access_token": new_token}), 200


@api.route("/auth/logout", methods=["DELETE"])
@jwt_required()
def modify_token():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    db.session.add(TokenBlocklist(jti=jti, created_at=now))
    db.session.commit()
    return jsonify(msg="JWT revoked")


@api.route("/auth/hello", methods=["GET"])
@jwt_required()
def hello():
    return jsonify(hello="world")
