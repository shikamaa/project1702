from flask import Flask
from os import getenv
from dotenv import load_dotenv
from flask_login import LoginManager 

load_dotenv()

def create_app() -> Flask:    
    app = Flask(__name__)
    app.secret_key = getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.from_mapping(
        CELERY = dict(
            broker_url=getenv('REDIS_URL'), 
            result_backend=getenv('REDIS_URL'))
    )
    return app

def create_login_manager(app: Flask) -> LoginManager:
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'simple_routes.login_page'
    login_manager.login_message = 'Please, log in for access'

    return login_manager

app = create_app()
login_manager = create_login_manager(app)

from db import db, migrate
db.init_app(app)
migrate.init_app(app,db)

import models

with app.app_context():
    #MIGRATE
    db.create_all()

from tasks import celery_init_app

celery_init_app(app)


from urls import teacher_bp, admin_bp, routes
from simple_urls import simple_routes
#handle_bad_request
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
# app.register_error_handler(400,handle_bad_request)

    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)