from app import create_app, db, fake
from app.models import Role, User, Post
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(dotenv_path)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app = create_app("development")
app_context = app.app_context()
app_context.push()
db.create_all()
Role.insert_roles()
fake.users(10)
fake.posts(10)

db.session.commit()
