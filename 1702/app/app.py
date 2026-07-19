from flask import Flask, flash, redirect, request, url_for
from os import getenv
from dotenv import load_dotenv
from flask_login import LoginManager
from tasks import celery_init_app
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
import logging


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
            task_time_limit=600
        ),
    )
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

    celery = celery_init_app(app)

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