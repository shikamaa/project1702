from flask import render_template, Blueprint, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_required, logout_user, current_user, login_user
from sqlalchemy import select
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequest
from datetime import timedelta
from db import db
from models import User, Task, Submission, UserType
from navigation import logged_user_menu, unlogged_user_menu
from functions import change_username, change_password
from tasks import  run_judge
import shutil
import uuid
import os
import pathlib
import logging

logger = logging.getLogger(__name__)

simple_routes = Blueprint('simple_routes', __name__, template_folder ='templates/student/')

@simple_routes.route("/task/<int:task_id>", methods=['GET', 'POST'])
@login_required
def task_detailed(task_id: int):
    current_task = db.session.get(Task, task_id)

    if current_task is None:
        abort(404)
    
    tests = list((current_task.test_cases or []) + (current_task.hidden_test_cases or []))

    if request.method == 'POST':
        file = request.files.get('file')

        if not file or not file.filename.endswith('.c'):
            flash("Only .c files are accepted")
            return redirect(url_for('simple_routes.compile_file', task_id = task_id))
    
        submission_directory = uuid.uuid4().hex

        container_uploads = "/uploads"
        upload_directory = os.path.join(container_uploads, submission_directory)

        try:
            os.makedirs(upload_directory,exist_ok=True)
            os.chmod(upload_directory, 0o777)
        except OSError:
            abort(500)

        source_code = file.read().decode('utf-8')
        file.seek(0)
        file.save(os.path.join(upload_directory, "solution.c"))

        script_path = pathlib.Path(__file__).parent / "s.sh"
        shutil.copy(script_path, upload_directory)  

        for test_number, test_case in enumerate(tests, start=1):
            input_data = test_case.get("input") or ""
            answer_data = test_case.get("output") or ""

            input_path = pathlib.Path(upload_directory) / f"{test_number}.in"
            input_path.write_text(input_data)

            answer_path = pathlib.Path(upload_directory) / f"{test_number}.ans"
            answer_path.write_text(str(answer_data))


        new_submission = Submission(
            user_id=int(current_user.user_id),
            task_id=current_task.task_id,
            code=source_code,
            celery_task_id = submission_directory,
            total_tests=len(tests)
        )

        db.session.add(new_submission)
        db.session.commit()

        celery_task  = run_judge.delay(tests,upload_directory, submission_directory, current_task.time_limit, \
                               current_task.memory_limit, new_submission.submission_id)
        
        new_submission.celery_task_id = celery_task.id
        db.session.commit()

        return redirect(url_for('simple_routes.submission_detailed', submission_id = new_submission.submission_id))

    return render_template(
        'task_detailed.html',
        title=f"Task {task_id}",
        task=current_task,
        menu=logged_user_menu()
    )
            
@simple_routes.get("/submission/<int:submission_id>/status")
@login_required
def submission_status(submission_id):
    query = select(Submission).where(Submission.submission_id == submission_id)

    sub = db.session.execute(query).scalar_one_or_none()
    if sub is None:
        abort(404)

    return jsonify({
        'status': sub.status.value, 
        'passed': sub.passed_tests,
        'total': sub.total_tests,
    })

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
    
@simple_routes.errorhandler(BadRequest)
def handle_bad_request(e):
    return ('bad request!', 400)

@simple_routes.route('/signup',  methods=['GET','POST'])
def signup_page():
    if current_user.is_authenticated:
        return redirect(url_for('simple_routes.show_tasks'))
    
    if request.method == 'POST':
        name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = db.session.execute(select(User).where(User.username == username)).scalar_one_or_none()

        if existing_user is not None:
            flash('User already exists')
            return render_template('registration_page.html', 
                                 title='Signup Page',
                                 menu=unlogged_user_menu())

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            first_name=name,
            last_name=last_name,
            user_role=UserType.STUDENT
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('simple_routes.show_tasks'))
        
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
            logger.info(f"User {username} logged in with success!")
            login_user(user, remember=True, duration=timedelta(minutes=30))
            return redirect(url_for('simple_routes.show_tasks'))
        
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
            change_password(new_password, current_password)
        elif 'new_username' in request.form:
            new_username = request.form.get('new_username')
            change_username(new_username)

    return render_template(
        'user_settings.html', 
        title='Settings',
        menu=logged_user_menu(),
        usr=current_user.username
        )
    
@simple_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('simple_routes.login_page'))

@simple_routes.get('/tasks')
@login_required
def show_tasks():
    query_active_tasks = select(Task).filter_by(is_active=True)
    task_list = db.session.execute(query_active_tasks).scalars().all()

    query_inactive_tasks = select(Task).filter_by(is_active=False)
    disabled_tasks_list = db.session.execute(query_inactive_tasks).scalars().all()

    return render_template(
        'task_list.html',
        title='Main page',
        menu=logged_user_menu(),
        tasks=task_list,
        disabled_tasks=disabled_tasks_list,
        usr = current_user.username
    )
    
@simple_routes.get('/user_submissions')
@login_required
def user_submissions():
    query = select(
        Submission.submission_id,
        Submission.task_id,
        Task.task_name,
        Submission.status,
        Submission.passed_tests,
        Submission.total_tests,
        Submission.submitted_at
    ).join(Task, Task.task_id == Submission.task_id)\
    .where(Submission.user_id == current_user.user_id)

    user_submissions = (db.session.execute(query)).all()    

    return render_template(
        'user_submissions.html',
        title='My submissions',
        menu = logged_user_menu(),
        columns = ['Task Name','Status','Tests','Submitted at', 'Details'],
        submissions = user_submissions
    )
    
@simple_routes.get('/submission/<int:submission_id>')
@login_required
def submission_detailed(submission_id):
    current_submission = db.session.get(Submission, submission_id)

    return render_template('submission_detailed.html',
                         title=f'Submission #{submission_id}',
                         menu=logged_user_menu(),
                         submission=current_submission,
    )
