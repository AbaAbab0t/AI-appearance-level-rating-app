  
from flask import Blueprint

api = Blueprint('api', __name__)

from . import posts, users, comments, errors, login, backstage, auth_jwt_ext,ai_app