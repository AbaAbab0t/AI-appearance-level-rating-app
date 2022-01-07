from flask import jsonify, request, g, url_for, current_app
from .. import db
from ..models import Post, Permission, User, Likes
from . import api
from .decorators import permission_required
from .errors import forbidden
from flask_cors import CORS, cross_origin


@api.route('/posts/')#获取所有文章（分页）参数：page页数
# @cross_origin()
def get_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(
        page, per_page=5,
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page+1)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/posts/<int:id>', methods=['GET'])#根据文章id获取文章
# @cross_origin()
def get_post(id):
    post = Post.query.get_or_404(id)
    author = db.session.query(User).filter_by(id=post.author_id).first()
    return jsonify({
        "post": post.to_json(),
        "author": author.to_json()
    })


@api.route('/posts/', methods=['POST'])#上传文章，返回存储位置及文章id
# @cross_origin()
# @permission_required(Permission.WRITE)
def new_post():
    post = Post.from_json(request.json)
    #post.author = g.current_user
    #post.author = g.current_user
    post.author_id=1
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, \
        {'Location': url_for('api.get_post', id=post.id)}


@api.route('/posts/<int:id>', methods=['PUT'])#编辑文章，返回修改后的文章内容（仅能修改文本）
# @cross_origin()
@permission_required(Permission.WRITE)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and \
            not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions')
    post.body = request.json.get('body', post.body)#body:修改完的内容(仅文本）
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json())


@api.route('/posts/<int:id>/getLikeNum', methods=['GET'])
def get_like_num(id):
    num = len(db.session.query(Likes).filter_by(post_id=id).all())
    return jsonify({
        "num": num
    })
