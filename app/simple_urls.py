from flask import render_template, Blueprint, redirect, url_for, request, flash, abort
from flask_login import login_required, logout_user, current_user, login_user
from sqlalchemy import select
from werkzeug.security import generate_password_hash, check_password_hash

from db import db
from model import Task, User, STUDENT, Submission
from navigation import logged_user_menu, unlogged_user_menu

simple_routes = Blueprint('simple_routes', __name__, template_folder ='../template')

@simple_routes.route('/')
def main_page():
    if current_user.is_authenticated:
        return redirect(url_for('simple_routes.show_tasks'))
    
    return render_template(
        'login_page.html', 
        title='1702 Main page',
        menu=unlogged_user_menu(),
        name=current_user
        )
    
@simple_routes.route('/signup',  methods=['GET','POST'])
def signup_page():
    if current_user.is_authenticated:
        return redirect(url_for('simple_routes.show_tasks'))
    
    if request.method == 'POST':
        name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('User already exists')
            return render_template('registration_page.html', 
                                 title='Signup Page',
                                 menu=unlogged_user_menu())

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            first_name=name,
            last_name=last_name,
            user_role=STUDENT
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('routes.tasks'))
        except Exception as e:
            db.session.rollback()
            flash('Database error')
            print(f'error {e}')

    return render_template(
        'registration_page.html', 
        title='Signup Page',
        menu=unlogged_user_menu()
        )

@simple_routes.route('/login', methods=['GET','POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('simple_routes.show_tasks'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('simple_routes.show_tasks'))
        
        flash('Incorrect username or password')

    return render_template(
        'login_page.html', 
        title='Login page',
        menu=unlogged_user_menu()
        )

@simple_routes.route('/settings', methods=['GET','POST'])
@login_required
def settings():   
    if request.method == 'POST':
        if 'new_password' in request.form:
            current_password = request.form.get('password')
            new_password = request.form.get('new_password')

            if check_password_hash(current_user.password_hash, current_password):
                current_user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash('Password successfully changed. Please log in again.')
                logout_user()
                return redirect(url_for('simple_routes.login_page'))
            else:
                flash('Incorrect current password!')

        elif 'new_username' in request.form:
            new_username = request.form.get('new_username')
            if not User.query.filter_by(username=new_username).first():
                current_user.username = new_username
                db.session.commit()
                flash('Username changed successfully')
            else:
                flash('Username already exists')

    return render_template(
        'user_settings.html', 
        title='Settings',
        menu=logged_user_menu(),
        usr=current_user.username
        )

# @simple_routes.get('/settings/<str:new_username>', methods=['GET', 'POST'])
# def change_username(new_username):
#     query = (
#         db.session.get(User.username, new_username)
#     )
#     if query is None:
#         flash("Coudn't change username. Username already exists")
#         return redirect(url_for('//'))
#     return render_template("...")
#     pass

    
@simple_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('simple_routes.login_page'))

@simple_routes.route('/tasks')
@login_required
def show_tasks():
    query = db.select(Task).filter_by(status = True)
    task_list = db.session.execute(query).scalars().all()   
    return render_template(
        'task_list.html',
        title='Main page',
        menu=logged_user_menu(),
        tasks=task_list,
        usr = current_user.username
    )

@simple_routes.get("/tasks/<int:task_id>")
@login_required
def show_task_detailed(task_id: int):
    task = db.session.get(Task, task_id)
    if task is None:
        abort(404)
    
    return render_template(
        'task_detailed.html',
        title=f'Task {task_id}',
        menu=logged_user_menu(),
        task=task,
        output=None,
        usr = current_user.user_role
    )
    
@simple_routes.route('/user_submissions')
@login_required
def user_submissions():
    query = (
        db.select(Submission).filter_by(user_id=current_user.user_id).order_by(Submission.submitted_at.desc())
    )
    user_submissions = db.session.execute(query).scalars().all()
    
    return render_template(
        'user_submissions.html',
        title='My submissions',
        menu = logged_user_menu(),
        submissions = user_submissions
        )