from flask import jsonify, request, g, url_for, current_app
from .. import db
from ..models import Post, Permission, User, Likes, Comment, Role
from . import api
from .decorators import permission_required
from .errors import forbidden
from flask_cors import CORS, cross_origin

@api.route("/backstage/user", methods=['POST'])
def post_user():
    user = User.from_json(request.json)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "success"})

@api.route("/backstage/user", methods=['PUT'])
def change_user():
    id = request.json.get('userid')
    db.session.query(User).filter_by(id=id).update({
        'username': request.json.get('username'),
        'email': request.json.get('email'),
        'avatar_hash': request.json.get('avatar'),
        'location': request.json.get('location'),
        'about_me': request.json.get('about_me')
    })
    db.session.commit()
    return jsonify({"user": db.session.query(User).filter_by(id=id).first().to_json()})

@api.route("/backstage/user", methods=['GET'])
def get_all_users():
    users = db.session.query(User).all()
    page = request.args.get('page', 1, type=int)
    pagination = User.query.paginate(
        page, per_page=8,
        error_out=False)
    page_users = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_all_users', page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_all_users', page=page + 1)
    total = len(users)
    return jsonify({
        "users": [user.backstageData() for user in page_users],
        "count": len(page_users),
        "total": total
    })

@api.route('/backstage/user', methods=['DELETE'])
def delete_user():
    id = request.args.get('id', type=int)
    db.session.query(User).filter_by(id=id).update({'hide': True})
    db.session.commit()
    return jsonify({"message": "success"})

@api.route('/backstage/recoverUser', methods=['POST'])
def recover_user():
    id = request.args.get('id', type=int)
    db.session.query(User).filter_by(id=id).update({'hide': False})
    db.session.commit()
    return jsonify({"message": "success"})


@api.route("/backstage/post", methods=['GET'])
def get_all_posts():
    posts = db.session.query(Post).all()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(
        page, per_page=8,
        error_out=False)
    page_posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_all_posts', page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_all_posts', page=page + 1)
    total = len(posts)
    return jsonify({
        "posts": [post.to_json() for post in page_posts],
        "count": len(page_posts),
        "total": total
    })


@api.route('/backstage/post', methods=['DELETE'])
def delete_post():
    id = request.args.get('id', type=int)
    db.session.query(Post).filter_by(id=id).update({'hide': True})
    db.session.commit()
    return jsonify({"message": "success"})

@api.route('/backstage/recoverPost', methods=['POST'])
def recover_post():
    id = request.args.get('id', type=int)
    db.session.query(Post).filter_by(id=id).update({'hide': False})
    db.session.commit()
    return jsonify({"message": "success"})

@api.route("/backstage/comment", methods=['GET'])
def get_all_comments():
    comments = db.session.query(Comment).all()
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.paginate(
        page, per_page=8,
        error_out=False)
    page_comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_all_comments', page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_all_comments', page=page + 1)
    total = len(comments)
    return jsonify({
        "comments": [comment.to_json() for comment in page_comments],
        "count": len(page_comments),
        "total": total
    })


@api.route('/backstage/comment', methods=['DELETE'])
def delete_comment():
    id = request.args.get('id', type=int)
    db.session.query(Comment).filter_by(id=id).update({'hide': True})
    db.session.commit()
    return jsonify({"message": "success"})

@api.route('/backstage/recoverComment', methods=['POST'])
def recover_comment():
    id = request.args.get('id', type=int)
    db.session.query(Comment).filter_by(id=id).update({'hide': False})
    db.session.commit()
    return jsonify({"message": "success"})

@api.route('/backstage/role', methods=['GET'])
def get_all_role():
    roles = db.session.query(Role).all()
    return jsonify({
        "roles": [role.to_json() for role in roles]
    })

@api.route('/backstage/getUserPermission', methods=['GET'])
def get_user_permission():
    id = request.args.get('id')
    user = db.session.query(User).filter_by(id=id).first()
    permission = db.session.query(Role).filter_by(id=user.role_id).first()
    return jsonify({
        "permission": permission.permissions
    })

@api.route('/backstage/getUserById', methods=['GET'])
def get_user_by_id():
    id = request.args.get('id')
    return jsonify(db.session.query(User).filter_by(id=id).first().to_json())





