from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
# from app.api.users import get_avasta
from app.exceptions import ValidationError
from . import db


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def to_json(self):
        json_data = {
            'id': self.id,
            'name': self.name,
            'default': self.default,
            'permissions': self.permissions
        }
        return json_data

    def __repr__(self):
        return '<Role %r>' % self.name


class Follow(db.Model):
    __tablename__ = 'follows'
    # id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def check_data(self, follower_id, followed_id):
        for follow in Follow.query.all():
            if follow.followed_id == followed_id and follow.follower_id == follower_id:
                return False
        return True

    def from_json(json_post):
        follower_id = json_post.get("follower_id")
        followed_id = json_post.get("followed_id")
        return Follow(follower_id=follower_id, followed_id=followed_id)

    def to_json(self):
        json_follow = {
            # 'url': url_for('api.get_user_followed', id=self.id),
            'followed_id': self.followed_id,
            'follower_id': self.follower_id,
        }
        return json_follow


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    face_rank = db.Column(db.Integer)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    hide = db.Column(db.Boolean, default=False)
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    avatar=db.Column(db.String(200))

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()
        if self.avatar_hash is None:
            self.avatar_hash = "https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"
        self.confirmed = True
        self.follow(self)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    @property
    def recommend(self):
        return db.session.query(User).filter(User.face_rank > 90)

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

    @property
    def favor_posts(self):
        return Post.query.join(Favorite, Favorite.post_id == Post.id)\
            .filter(Favorite.user_id == self.id)

    def all_users(self):
        return User.query.order_by(id)

    @property
    def liked_posts(self):
        return Post.query.join(Likes, Likes.post_id == Post.id) \
            .filter(Likes.user_id == self.id)

    def to_json(self):
        json_user = {
            # 'url': url_for('api.get_user', id=self.id),
            'username': self.username,
            'userid': self.id,
            'avatar': url_for('static', filename=self.avatar),
            'about_me': self.about_me
            # 'member_since': self.member_since,
            # 'last_seen': self.last_seen,
            # 'posts_url': url_for('api.get_user_posts', id=self.id),
            # 'followed_posts_url': url_for('api.get_user_followed_posts',
            #                              id=self.id),
            # 'post_count': self.posts.count()
        }
        return json_user

    def backstageData(self):
        json_user = {
            'username': self.username,
            'userid': self.id,
            'avatar': url_for('static', filename=self.avatar),
            'about_me': self.about_me,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'roleid': self.role_id,
            'location': self.location,
            'facerank': self.face_rank,
            'email': self.email
        }
        return json_user

    @staticmethod
    def from_json(json_post):
        username = json_post.get("username")
        password_hash = json_post.get("password_hash")
        email = json_post.get("email")
        return User(username=username, password_hash=password_hash, email=email)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


# login_manager.anonymous_user = AnonymousUser


# @login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    pic = db.Column(db.String(200))
    stars = db.Column(db.Integer, default=0)
    face_mark = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    confirmed = db.Column(db.Boolean, default=True)
    hide = db.Column(db.Boolean, default=False)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', '2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
            'comments_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments.count(),
            'postid': self.id,
            'picture': self.pic
        }
        return json_post

    def backstage_data(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
            'comments_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments.count(),
            'postid': self.id,
            'picture': self.pic
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)

    def star(self):
        self.star = self.star+1
        db.session.add(self)

    def unstar(self, post):
        if self.star > 0:
            self.star = self.star-1
            db.session.add(self)


db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    confirmed = db.Column(db.Boolean, default=True)
    hide = db.Column(db.Boolean, default=False)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id),
            'post_url': url_for('api.get_post', id=self.post_id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_id': self.author_id,
            'id': self.id
            # 'author_url': url_for('api.get_user', id=self.author_id)
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        author_id = json_comment.get('author_id')
        return Comment(body=body, author_id=author_id, body_html=body, disabled=0)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Favorite(db.Model):
    __tablename__ = 'favorite'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    post_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def add_favorite(self, user_id, post_id):
        if not self.is_favorite(user_id, post_id):
            f = Favorite(user_id=user_id, post_id=post_id)
            db.session.add(f)

    def del_favorite(self, user_id, post_id):
        f = self.filter_by(user_id=user_id, post_id=post_id).first()
        if f:
            db.session.delete(f)

    def is_favorite(self, user_id, favorite_id):
        return db.session.query(Favorite).filter_by(user_id=user_id, post_id=favorite_id).first()

    def from_json(json_post):
        user_id = json_post.get("user_id")
        post_id = json_post.get("post_id")
        return Favorite(user_id=user_id, post_id=post_id)


class Likes(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    post_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def from_json(json_post):
        user_id = json_post.get("user_id")
        post_id = json_post.get("post_id")
        return Likes(user_id=user_id, post_id=post_id)


class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)


class FaceLandMark(db.Model):
    __tablename__ = 'facelandmark'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    face_landmark = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Get face feature
class FaceFeature(db.Model):
    __tablename__ = 'facefeature'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    face_feature = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Recomendation
class Recomendation(db.Model):
    __tablename__ = 'recomendation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    friends_id = db.Column(db.Integer)
    accept= db.Column(db.Boolean)

