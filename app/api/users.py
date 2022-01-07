from flask import jsonify, request, current_app, url_for
from numpy.lib.function_base import average
from . import api
from ..models import User, Post, Follow, Favorite, Likes
from ..import db
from flask_cors import CORS, cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import rdb1
import json

@api.route('/users/<int:id>', methods=["GET"])#获取用户信息
# @cross_origin()
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())



@api.route('/users/<int:id>/posts')#获取用户文章 参数page页数
# @cross_origin()
def get_user_posts(id):
    user = User.query.get_or_404(id)
    Posts = db.session.query(Post).filter_by(author_id=id).order_by(Post.timestamp.desc()).all()
    return jsonify({
        "posts": [post.to_json() for post in Posts]
    })
    #page = request.args.get('page', 1, type=int)  #键值对page:xxx
    # pagination = user.posts.filter_by(author_id=id).order_by(Post.timestamp.desc()).paginate(
    #     page, per_page=5,
    #     error_out=False)
    # posts = pagination.items
    # prev = None
    # if pagination.has_prev:
    #     prev = url_for('api.get_user_posts', id=id, page=page-1)
    # next = None
    # if pagination.has_next:
    #     next = url_for('api.get_user_posts', id=id, page=page+1)
    # return jsonify({
    #     'posts': [post.to_json() for post in posts],
    #     'prev': prev,
    #     'next': next,
    #     'count': pagination.total
    # })



@api.route('/users/<int:id>/followers', methods=['GET']) #获取粉丝信息
# @cross_origin()
def get_user_follower(id):
    follows = db.session.query(Follow).filter(Follow.followed_id==id).all()
    userDatas=[]
    for follow in follows:
        userData = db.session.query(User).filter_by(id=follow.follower_id).first()
        userDatas.append(userData)
    total = len(userDatas)
    return jsonify({
        "data": [user.to_json() for user in userDatas],
        "total": total
    })

    # page = request.args.get('page', 1, type=int)
    # pagination = follow.order_by(Follow.follower_id).paginate(
    #     page, per_page=5,
    #     error_out=False)
    # followers = pagination.items
    # prev = None
    # if pagination.has_prev:
    #     prev = url_for('api.get_user_follower', id=Follow.followed_id, page=page - 1)
    # next = None
    # if pagination.has_next:
    #     next = url_for('api.get_user_follower', id=Follow.followed_id, page=page + 1)
    # return jsonify({
    #     'posts': [follower.to_json() for follower in followers],
    #     'prev': prev,
    #     'next': next,
    #     'count': pagination.total
    # })

@api.route('/users/<int:id>/followed', methods=['GET']) #获取关注的用户信息
# @jwt_required()
def get_user_followed(id):
    follows = db.session.query(Follow).filter(Follow.follower_id == id).order_by(Follow.timestamp.desc()).all()
    userDatas = []
    for follow in follows:
        userData = db.session.query(User).filter_by(id=follow.followed_id).first()
        userDatas.append(userData)
    total = len(userDatas)
    return jsonify({
        "data": [user.to_json() for user in userDatas],
        "total": total
    })
    # follow = db.session.query(Follow).filter(Follow.follower_id==id)
    # page = request.args.get('page', 1, type=int)
    # pagination = follow.order_by(Follow.followed_id).paginate(
    #     page, per_page=5,
    #     error_out=False)
    # followeds = pagination.items
    # prev = None
    # if pagination.has_prev:
    #     prev = url_for('api.get_user_followed', id=Follow.follower_id, page=page - 1)
    # next = None
    # if pagination.has_next:
    #     next = url_for('api.get_user_followed', id=Follow.follower_id, page=page + 1)
    # return jsonify({
    #     'posts': [followed.to_json() for followed in followeds],
    #     'prev': prev,
    #     'next': next,
    #     'count': pagination.total
    # })

@api.route('/users/<int:id>/follow', methods=['POST']) #关注用户
# @cross_origin()
def user_follow(id):
    follow = Follow.from_json(request.json)
    db.session.add(follow)
    db.session.commit()
    return jsonify(follow.to_json())
#
@api.route('/users/<int:id>/unfollow', methods=['DELETE']) #取消关注
# @cross_origin()
def user_unfollow(id):
    follower_id = request.json.get("follower_id")
    followed_id = request.json.get("followed_id")
    db.session.query(Follow).filter_by(followed_id=followed_id).filter_by(follower_id=follower_id).delete()
    db.session.commit()
    return jsonify({"message":"success"})

@api.route('/users/<int:id>/followedUserPosts', methods=['GET']) #获取用户关注的用户的文章及关注的用户信息
# @cross_origin()
def get_user_followeds_posts(id):
    user = User.query.get_or_404(id)
    #posts = user.followed_posts.order_by(Post.timestamp.desc()).all()
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=5,
        error_out=False)
    followeds = pagination.items
    count = len(followeds)
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_followed_posts', id=id, page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_followed_posts', id=id, page=page + 1)
    return jsonify({
        'posts': [followed.to_json() for followed in followeds],
        'userData': [db.session.query(User).filter_by(id=followed.author_id).first().to_json() for followed in followeds],
        'prev': prev,
        'next': next,
        'count': count,
        'total': pagination.total
    })

@api.route('/users/<int:id>/favorPost', methods=['POST']) #收藏文章
# @cross_origin()
def favor_post(id):
    favorite = Favorite.from_json(request.json)
    db.session.add(favorite)
    db.session.commit()
    return jsonify({"message":"success"})

@api.route('/users/<int:id>/unfavorPost', methods=['DELETE']) #取消收藏文章
# @cross_origin()
def unfavor_post(id):
    user_id = request.json.get("user_id")
    post_id = request.json.get("post_id")
    db.session.query(Favorite).filter_by(user_id=user_id).filter_by(post_id=post_id).delete()
    db.session.commit()
    return jsonify({"message": "success"})

@api.route('/users/<int:id>/favor_posts') #获取用户收藏的文章
# @cross_origin()
def get_user_followed_posts(id):
    user = User.query.get_or_404(id)
    posts = user.favor_posts.order_by(Post.timestamp.desc()).all()
    return jsonify({
        "posts": [post.to_json() for post in posts],
        "users": [db.session.query(User).filter_by(id=post.author_id).first().to_json() for post in posts]
    })
    # page = request.args.get('page', 1, type=int)
    # pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(
    #     page, per_page=5,
    #     error_out=False)
    # posts = pagination.items
    # prev = None
    # if pagination.has_prev:
    #     prev = url_for('api.get_user_followed_posts', id=id, page=page-1)
    # next = None
    # if pagination.has_next:
    #     next = url_for('api.get_user_followed_posts', id=id, page=page+1)
    # return jsonify({
    #     'posts': [post.to_json() for post in posts],
    #     'prev': prev,
    #     'next': next,
    #     'count': pagination.total
    # })



@api.route('/users/<int:id>/likePost', methods=['POST']) #点赞
# @cross_origin()
def like_post(id):
    # like = Likes.from_json(request.json)
    post_id = request.json.get("post_id")
    like = Likes(post_id=post_id, user_id=id)
    db.session.add(like)
    db.session.commit()
    return jsonify({"message": "success"})


@api.route('/users/<int:id>/unlikePost', methods=['DELETE'])#取消点赞
# @cross_origin()
def unlike_post(id):
    user_id = request.json.get("user_id")
    post_id = request.json.get("post_id")
    db.session.query(Likes).filter_by(user_id=user_id).filter_by(post_id=post_id).delete()
    db.session.commit()
    return jsonify({"message": "success"})

@api.route('/users/<int:id>/likedPosts', methods=['GET'])#获取用户点赞过的文章id
# @cross_origin()
def get_user_liked_posts_id(id):
    likes = db.session.query(Likes).filter_by(user_id=id).all()
    return jsonify({
        "postid": [like.post_id for like in likes]
    })


@api.route('/users/<int:id>/likedPostsContent', methods=['GET'])
def get_user_liked_posts(id):
    likes = db.session.query(Likes).filter_by(user_id=id).all()
    posts = [db.session.query(Post).filter_by(id=like.post_id).first() for like in likes]
    return jsonify({
        "posts": [post.to_json() for post in posts],
        "authors": [db.session.query(User).filter_by(id=post.author_id).first().to_json() for post in posts],
        "count": len(likes)
    })

@api.route('/users/<int:id>/recommendFollow', methods=['GET']) #推荐好友
def recommend_follow(id):
    recommend = []
    user = User.query.get_or_404(id)
    fits = user.recommend.order_by(User.id).all()
    for fit in fits:
        if db.session.query(Follow).filter_by(follower_id=id).filter_by(followed_id=fit.id).first() is None:
            recommend.append(fit)
    return jsonify({
        "recommend": [user.to_json() for user in recommend]
    })

@api.route('/users/<int:id>/followedUserId') #获取关注的用户id
def get_followed_user_id(id):
    follows = db.session.query(Follow).filter(Follow.follower_id == id).order_by(Follow.timestamp.desc()).all()
    userDatas = []
    for follow in follows:
        userData = db.session.query(User).filter_by(id=follow.followed_id).first()
        userDatas.append(userData)
    total = len(userDatas)
    return jsonify({
        "id": [user.id for user in userDatas]
    })

def get_avasta(avatar):
    if avatar.startswith('http'):
        avatar = avatar
    else:
        avatar = url_for('static', filename=avatar)
    return avatar

@api.route('/users/info/<int:id>') #获取用户信息
#@jwt_required()
def get_user_info(id):
    cur_id = id
    #cur_id=get_jwt_identity()
    cur_user = User.query.get_or_404(cur_id)
    cur_avatar=get_avasta(cur_user.avatar)


    recommands=json.loads(rdb1.get(cur_id))
    recommandation=[]
    for id,sim in recommands.items():
        user = User.query.get_or_404(id)
        avatar=get_avasta(user.avatar)
        username=user.username
        recommandation.append({"id":id,"avatar":avatar,"username":username,"sim":sim})

    return jsonify({
    "id": cur_id,
    "username": cur_user.username,
    "beauty": cur_user.face_rank,
    "avatar":cur_avatar,
    "recommandation": recommandation,
    })


@api.route('/users/<int:id>/recommandUser', methods=['GET'])
def get_recommand_user(id):
    recommands= json.loads(rdb1.get(id))
    recommandation = []
    for id,sim in recommands.items():
        user = User.query.get_or_404(id)
        avatar=get_avasta(user.avatar)
        username=user.username
        recommandation.append({"id":id,"avatar":avatar,"username":username,"sim":sim})
    return jsonify({
        "recommandation": recommandation
    })






