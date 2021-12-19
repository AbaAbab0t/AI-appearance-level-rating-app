from flask import jsonify, request, g, url_for, current_app
from .. import db
from ..models import Post, Permission, Comment, User
from . import api
from .decorators import permission_required
from flask_cors import CORS, cross_origin


@api.route('/comments/')#所有评论列表，返回所有评论（分页，好像是默认的20一页）
@cross_origin()
def get_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=5,
        error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page+1)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/comments/<int:id>')#根据评论id获取评论
@cross_origin()
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())


@api.route('/posts/<int:id>/comments/')#根据文章id获取对应的评论列表
@cross_origin()
def get_post_comments(id):
    post = Post.query.get_or_404(id)
    comments = post.comments.order_by(Comment.timestamp.asc()).all()
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'comment_author': [db.session.query(User).filter_by(id=comment.author_id).\
                               first().to_json() for comment in comments],
        'total': len(comments)
    })


@api.route('/posts/<int:id>/comments', methods=['POST'])#上传某id文章下的评论，返回存储位置和评论id
@cross_origin()
# @permission_required(Permission.COMMENT)
def new_post_comment(id):
    post = Post.query.get_or_404(id)
    comment = Comment.from_json(request.json)
    comment.post_id = id
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json())
