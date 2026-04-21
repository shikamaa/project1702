from flask import flash, redirect,url_for
from sqlalchemy import select
from db import db
from flask_login import current_user
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
import re
from models import Submission

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
            
def parse_time_output(stderr):
    time_match = re.search(r'Elapsed.*?: (\d+):(\d+)\.(\d+)', stderr)
    mem_match = re.search(r'Maximum resident set size.*?: (\d+)', stderr)

    if not time_match or not mem_match:
        return 0, 0

    minutes = int(time_match.group(1))
    seconds = int(time_match.group(2))
    centiseconds = int(time_match.group(3))

    elapsed = minutes * 60 + seconds + centiseconds / 100

    memory = int(mem_match.group(1))

    return elapsed, memory


def make_submission(us_id,t_id,code,verdict, passed_tests, total_tests):    
    new_submission = Submission(
        user_id=us_id,
        task_id=t_id,
        code=code,
        status=verdict,
        passed_tests=passed_tests,
        total_tests=total_tests,
    )
    db.session.add(new_submission)
    db.session.commit()
    return new_submission

