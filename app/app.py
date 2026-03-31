from flask import Flask
from os import getenv
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from flask_login import LoginManager 
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'simple_routes.login_page'
login_manager.login_message = 'Please, log in for access'

from db import db
db.init_app(app)

import models

with app.app_context():
    db.create_all()

from urls import teacher_bp, admin_bp, routes
from simple_urls import simple_routes
from admin_urls import admin_routes

from teacher_urls import teacher_urls

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(models.User, int(user_id)) 
    
app.register_blueprint(routes)
app.register_blueprint(teacher_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(simple_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(teacher_urls)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)