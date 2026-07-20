from flask import flash, redirect,url_for
from sqlalchemy import select
from db import db
from flask_login import current_user
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter.util import get_remote_address

def get_user_or_ip():
    if current_user.is_authenticated:
        return f"{current_user.user_id}"
    return get_remote_address()

def change_username(new_username):
    if current_user.username == new_username:
        flash(f'You are already {new_username}')
        return redirect(url_for('simple_routes.settings'))
    query = select(User).where(User.username == new_username)
    search_usernames = db.session.execute(query).scalar_one_or_none()
    if search_usernames is None:
        current_user.username = new_username
        db.session.commit()
        flash('Username changed successfully')
    else:
        flash('Username already exists')
    return redirect(url_for('simple_routes.settings'))

def change_password(new_password, current_password):
        if check_password_hash(current_user.password_hash, current_password):
            current_user.password_hash = generate_password_hash(new_password)
            flash('Password changed successfully!')
            db.session.commit()
            return redirect(url_for('simple_routes.settings'))
        else:
            flash('No match')

