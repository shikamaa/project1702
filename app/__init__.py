from flask import Flask, flash, redirect, request, url_for
from flask_login import LoginManager, current_user
from flask_limiter import Limiter
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import TooManyRequests
import logging
from os import getenv
from dotenv import load_dotenv
from celery import Celery, Task

from utils.accounts import get_user_or_ip

limiter = Limiter(
    key_func=get_user_or_ip,
    default_limits=[],
)

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args:object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args,**kwargs)
            
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
          
def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = getenv('SECRET_KEY')
    if not app.secret_key:
        raise RuntimeError(
            "SECRET_KEY is not set. Copy .env.example to .env and fill it in. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    CSRFProtect(app)

    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.from_mapping(
        CELERY=dict(
            broker_url=getenv('CEL_BROKER'),
            result_backend=getenv('CEL_BACKEND'),
            task_ignore_result=True,
            task_time_limit=300
        ),
    )
    app.config.from_prefixed_env()
    celery_init_app(app)
    app.config["RATELIMIT_STORAGE_URI"] = getenv('CEL_BROKER')
    app.config["RATELIMIT_STRATEGY"] = "moving-window"
    limiter.init_app(app)

    @app.errorhandler(TooManyRequests)
    def handle_rate_limit(e):
        app.logger.warning(
            f'Rate limit hit: endpoint={request.endpoint} '
            f'user={current_user.user_id if current_user.is_authenticated else request.remote_addr}'
        )
        flash('Too many submissions, please wait a bit')
        return redirect(request.referrer or url_for('simple_routes.main_page'))
    
    from simple_urls import simple_routes
    from teacher_urls import teacher_urls
    from admin_urls import admin_routes

    app.register_blueprint(simple_routes)
    app.register_blueprint(admin_routes)
    app.register_blueprint(teacher_urls)

    from db import db
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'simple_routes.login_page'
    login_manager.login_message = 'Please, log in for access'

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    logging.basicConfig(
        filename='./logs/app.log',
        level=logging.INFO,
        format='%(levelname)s: %(message)s (%(filename)s:%(lineno)d)'
    )

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.warning(
            f'CSRF rejected: endpoint={request.endpoint} '
            f'path={request.path} reason="{e.description}" '
            f'has_token_field={"csrf_token" in request.form}'
        )
        flash('The form expired, please try again')
        return redirect(request.referrer or url_for('simple_routes.main_page'))

    return app

