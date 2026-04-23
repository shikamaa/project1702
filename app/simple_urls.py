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

from tasks import test, run_judge
import subprocess
import shutil
import uuid
import os
import pathlib

simple_routes = Blueprint('simple_routes', __name__, template_folder ='templates/student/')

"""

task = [
    {
      "input": 1,
      "output": 2  
    },
    {
      "input": 2,
      "output": 4          
    },
]
filename = 'Dockerfile'
parent_dir = os.path.realpath("") 


dir = 'temp'
title = uuid.uuid4().hex
full_path = os.path.join(parent_dir, dir)
#print(full_path)

import pathlib
# structured_path = full_path[0:len(full_path)-len(dir)]
# final_path = os.path.join(structured_path,dir)
# print(final_path)
# try:
#     os.makedirs(structured_path, exist_ok=True)
# except OSError as ose:
#     print(ose)

dirs = pathlib.Path.cwd()
a = dirs.parent

upload_dir = os.path.join(a,str(title))
try:
    os.makedirs(upload_dir,exist_ok=True)
except OSError as OSerr:
    print(OSerr)


for num, test_case in enumerate(task, start= 1):
    path1 = pathlib.Path(upload_dir) / f"{num}.in"
    path1.write_text(str(test_case["input"]))
    
    path2 = pathlib.Path(upload_dir) / f"{num}.ans"
    path2.write_text(str(test_case["output"]))




shutil.copy("a.c", upload_dir)
shutil.copy("s.sh", upload_dir)

docker_tester = subprocess.run([
    "docker", "run", "--rm",
    "-v", f"{upload_dir}:/box",
    "--network=none",
    "judge",
    "sh", "/box/s.sh", "/box/a.c",
],text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

# print(docker_tester.stdout)
# print(docker_tester.stderr)
# print(docker_tester.returncode)

for num, test_case in enumerate(task, start=1):
    out_path = pathlib.Path(upload_dir) / f"{num}.out"
    ans_path = pathlib.Path(upload_dir) / f"{num}.ans"
    
    out = out_path.read_text().strip()
    ans = ans_path.read_text().strip()
    
    if out == ans:
        print(f"Test {num}: AC")
    else:
        print(f"Test {num}: WA | got: {out} | expected: {ans}")


"""


@simple_routes.route("/task/<int:task_id>", methods=['GET', 'POST'])
@login_required
def new_task_det(task_id):
    current_task = db.session.execute(
        select(Task).where(Task.task_id == task_id)
    ).scalars().one_or_none()

    if current_task is None:
        abort(404)
    

    tests = list((current_task.hidden_test_cases or []) + (current_task.test_cases or []))
    if request.method == 'POST':
        file = request.files.get('file')

        if not file or not file.filename.endswith('.c'):
            flash("Only .c files are accepted")
            return redirect(url_for('simple_routes.new_task_det', task_id=task_id))
    
        submission_directory = uuid.uuid4().hex
        directories = pathlib.Path.cwd()
        parent_directories = directories.parent

        upload_directory = os.path.join(parent_directories, str(submission_directory))

        try:
            os.makedirs(upload_directory,exist_ok=True)
        except OSError as OSerr:
            print(OSerr)   
        file.save(os.path.join(upload_directory, "solution.c"))
        for test_number, test_case in enumerate(tests, start=1):
            input_path = pathlib.Path(upload_directory) / f"{test_number}.in"      
            input_path.write_text(str(test_case["input"]))

            answer_path = pathlib.Path(upload_directory) / f"{test_number}.ans"      
            answer_path.write_text(str(test_case["output"]))

        shutil.copy("s.sh", upload_directory)    

        print(upload_directory)
        print(os.listdir(upload_directory))

        docker_tester = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{upload_directory}:/box",
            "--network=none",
            "judge",
            "sh", "/box/s.sh", "/box/solution.c",
        ],text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        for test_number, test_case in enumerate(tests, start=1):
            out_path = pathlib.Path(upload_directory) / f"{test_number}.out"
            ans_path = pathlib.Path(upload_directory) / f"{test_number}.ans"
            
            out = out_path.read_text().strip()
            ans = ans_path.read_text().strip()
            
            if out == ans:
                print(f"Test {test_number}: AC")
            else:
                print(f"Test {test_number}: WA | got: {out} | expected: {ans}")

    return render_template(
        'new_det_task.html',
        task=current_task,
        menu=logged_user_menu()
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
    