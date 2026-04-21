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

simple_routes = Blueprint('simple_routes', __name__, template_folder ='templates/student/')

@simple_routes.route("/task/<int:task_id>", methods=['GET', 'POST'])
@login_required
def new_task_det(task_id):
    current_task = db.session.execute(
        select(Task).where(Task.task_id == task_id)
    ).scalars().one_or_none()
    
    if current_task is None:
        abort(404)
    
    if request.method == 'POST':
        file = request.files.get('file')

        if not file or not file.filename.endswith('.c'):
            flash("Only .c files are accepted")
            return redirect(url_for('simple_routes.new_task_det', task_id=task_id))

        submission_id = uuid.uuid4().hex
        local_dir = os.path.join(os.getenv('FILEPATH'), submission_id) 
        host_dir = os.path.join(os.getenv('HOST_UPLOADS'), submission_id)
        
        
        os.makedirs(local_dir, exist_ok=True)
        filepath = os.path.join(local_dir, 'solution.c')
        file_tests = (current_task.test_cases or []) + (current_task.hidden_test_cases + [])
        
        run_judge.delay(file_tests)
        code_content = ""
        
        try:
            code_content = file.read().decode('utf-8')
            file.seek(0)
            file.save(filepath)
            
            final_verdict = 'Accepted for testing'
            passed_count = 0
            
            compile_proc = subprocess.run([
                'docker', 'run', '--rm',
                '--network=none',
                '-v', f'{host_dir}:/box',
                'gcc:latest', 
                'sh', '-c', 'gcc /box/solution.c -o /box/solution'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if compile_proc.returncode != 0:
                final_verdict = 'CE'
            else:
                open_tests = current_task.test_cases or []
                hidden_tests = current_task.hidden_test_cases or []
                all_tests = open_tests + hidden_tests
                
                for test_data in all_tests:
                    test_input = test_data.get("input", "")
                    expected_output = test_data.get("output", "").strip()
                    
                    try:
                        result = subprocess.run([
                            'docker', 'run', '--rm', '-i',
                            f'--memory={current_task.memory_limit}m',
                            '--cpus=0.5',
                            '--pids-limit=64',
                            '--network=none',
                            '-v', f'{host_dir}:/box',
                            'judge',
                            'sh', '-c', '/usr/bin/time -v /box/solution'
                        ],
                        input=test_input,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=current_task.time_limit + 2 
                        )
                        
                        elapsed, memory_kb = parse_time_output(result.stderr)
                        
                        if elapsed > current_task.time_limit:
                            final_verdict = 'TLE'
                            break
                        
                        if memory_kb > current_task.memory_limit * 1024:
                            final_verdict = 'MLE'
                            break

                        if result.returncode != 0:
                            final_verdict = 'RE'
                            break
                        
                        actual_output = result.stdout.strip()
                        if actual_output == expected_output:
                            passed_count += 1
                        elif expected_output in actual_output.strip():
                            final_verdict = 'PE'
                        else:
                            final_verdict = 'WA'
                            break
                            
                    except subprocess.TimeoutExpired:
                        final_verdict = 'TLE'
                        break
                    except Exception as e:
                        print(f"Execution error: {e}")
                        final_verdict = 'RE'
                        break
              
            total_tests_count = len(current_task.test_cases or []) + len(current_task.hidden_test_cases or [])
            if passed_count == total_tests_count:
                final_verdict = 'OK'
            elif passed_count > 0:
                final_verdict = 'PS'

            subm = make_submission(current_user.user_id, current_task.task_id, code_content, final_verdict,passed_count, total_tests_count)
            
            flash(f"Submission finished with status: {final_verdict}")
            return redirect(url_for('simple_routes.submission_detailed', submission=subm.submission_id))

        except Exception as e:
            db.session.rollback()
            flash(f"Internal error: {str(e)}")
            return redirect(url_for('simple_routes.new_task_det', task_id=task_id))

        finally:
            if os.path.exists(local_dir):
                shutil.rmtree(local_dir, ignore_errors=True)
            
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
    