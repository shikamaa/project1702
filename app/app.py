from flask import Flask
from os import getenv
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from flask_login import LoginManager
from login import * 
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'routes_bp.login_page'
login_manager.login_message = 'Please, log in for access'

from db import db
from routes import routes, teacher_bp, admin_bp

import models
with app.app_context():
    db.init_app(app)
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

app.register_blueprint(routes)
app.register_blueprint(teacher_bp)
app.register_blueprint(admin_bp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)