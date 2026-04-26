from flask import render_template, Blueprint, redirect, url_for, request, flash, abort
from flask_login import login_required, logout_user, current_user, login_user
from sqlalchemy import select
from sqlalchemy.orm import joinedload, load_only
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequest
from datetime import timedelta
from db import db
from models import Task, User, STUDENT, Submission, TEACHER, ADMIN, SubmissionReview
from navigation import logged_user_menu, unlogged_user_menu
from functions import change_username, change_password, parse_time_output, make_submission

from tasks import  run_judge
import subprocess
import shutil
import uuid
import os
import pathlib

simple_routes = Blueprint('simple_routes', __name__, template_folder ='templates/student/')

@simple_routes.route("/task/<int:task_id>", methods=['GET', 'POST'])
@login_required
def new_task_det(task_id):
    current_task = db.session.execute(
        select(Task).where(Task.task_id == task_id)
    ).scalars().one_or_none()

    if current_task is None:
        abort(404)
    

    tests = list((current_task.hidden_test_cases or []) + (current_task.test_cases or []))
    results = []
    if request.method == 'POST':
        file = request.files.get('file')

        if not file or not file.filename.endswith('.c'):
            flash("Only .c files are accepted")
            return redirect(url_for('simple_routes.new_task_det', task_id=task_id))
    
        submission_directory = uuid.uuid4().hex

        container_uploads = "/uploads"
        upload_directory = os.path.join(container_uploads, submission_directory)

        try:
            os.makedirs(upload_directory,exist_ok=True)
            os.chmod(upload_directory, 0o777)
        except OSError as OSerr:
            abort(500)
            print(OSerr)

        file.save(os.path.join(upload_directory, "solution.c"))
        for test_number, test_case in enumerate(tests, start=1):
            input_path = pathlib.Path(upload_directory) / f"{test_number}.in"      
            input_path.write_text(str(test_case["input"]))

            answer_path = pathlib.Path(upload_directory) / f"{test_number}.ans"      
            answer_path.write_text(str(test_case["output"]))

        script_path = pathlib.Path(__file__).parent / "s.sh"
        shutil.copy(script_path, upload_directory)  

        # print(upload_directory)
        # print(os.listdir(upload_directory))
        results = run_judge(tests,upload_directory, submission_directory)

        print(results)
        
    return render_template(
        'new_det_task.html',
        task=current_task,
        menu=logged_user_menu(),
        result = results,
    )
            
        
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
            print('ACCOUNT EXISTS')
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

@simple_routes.route('/tasks')
@login_required
def show_tasks():
    query = select(Task).filter_by(status = True)
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
        usr = current_user.user_role.name 
    )
    
@simple_routes.route('/user_submissions')
@login_required
def user_submissions():

    query = (
            select(Submission).where(Submission.user_id == current_user.user_id).
            options(load_only(Submission.submission_id, Submission.status, Submission.submitted_at, Submission.passed_tests, Submission.total_tests),
            joinedload(Submission.task).load_only(Task.task_name)).order_by(Submission.submitted_at.desc())
            )
    
    user_submissions = (db.session.execute(query)).scalars().all()    

    
    return render_template(
        'user_submissions.html',
        title='My submissions',
        menu = logged_user_menu(),
        columns = ['Task Name','Status','Tests','Submitted at', 'Details'],
        submissions = user_submissions
    )
    
@simple_routes.route('/submission/<int:submission_id>')
@login_required
def submission_detailed(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    
    
    return render_template('submission_detailed.html',
                         title=f'Submission #{submission_id}',
                         menu=logged_user_menu(),
                         submission=submission,
                         )
    