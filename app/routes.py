from flask import render_template, request, redirect, url_for, session, flash, Blueprint
import os
import subprocess
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from nav import unlogged_user_menu, logged_user_menu
from models import User, Submission, Task
from database1702 import db

import time


routes_bp = Blueprint('routes_bp',  __name__, url_prefix='/student')

@routes_bp.route('/')
def main_page():
    return render_template('login.html', title='Docker 1702 Main page')


@routes_bp.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', title='Signup Page', error='User already exists', menu=unlogged_user_menu())

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            first_name=name,
            last_name=last_name,
            is_admin=0
        )
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Database error')
            return render_template('signup.html', title='Signup Page', error='Database error', menu=unlogged_user_menu())

        session['user_in_session'] = new_user.username
        session.permanent = True
        return redirect(url_for('routes_bp.tasks'))

    return render_template('signup.html', title='Signup Page', menu=logged_user_menu())

@routes_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    error_message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.permanent = True
            session['user_in_session'] = user.username
            return redirect(url_for('routes_bp.tasks'))
        error_message = 'Incorrect username or password'

    return render_template('login.html', title='Docker Login page', error=error_message, menu=unlogged_user_menu())

@routes_bp.route('/logout')
def logout():
    session.pop('user_in_session', None)
    return redirect(url_for('routes_bp.login_page'))

@routes_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_in_session' not in session:
        flash('User is not authorized')
        return redirect(url_for('routes_bp.login_page'))

    user_in_session = session['user_in_session']
    current_user = User.query.filter_by(username=user_in_session).first()

    if request.method == 'POST':
        if 'new_password' in request.form:
            current_password = request.form.get('password')
            new_password = request.form.get('new_password')

            if current_user and check_password_hash(current_user.password_hash, current_password):
                current_user.change_password(new_password)
                db.session.commit()
                flash('Password successfully changed. Please log in again.')
                session.pop('user_in_session', None)
                return redirect(url_for('routes_bp.login_page'))
            else:
                flash('Incorrect current password!')

        elif 'new_username' in request.form:
            new_username = request.form.get('new_username')
            if not User.query.filter_by(username=new_username).first():
                current_user.change_username(new_username)
                db.session.commit()
                flash('Username changed successfully')
                session['user_in_session'] = new_username
            else:
                flash('Username already exists')

    return render_template('settings.html', title='Settings', user=user_in_session, menu=logged_user_menu())

@routes_bp.route('/tasks')
def tasks():
    if 'user_in_session' not in session:
        return redirect(url_for('routes_bp.login_page'))
    user = session['user_in_session']
    all_tasks = Task.query.all()
    return render_template('tasks.html', title='Main page', user=user, menu=logged_user_menu(), tasks=all_tasks)


@routes_bp.route('/tasks/<int:task_id>')
def task_detailed(task_id):
    if 'user_in_session' not in session:
        return redirect(url_for('routes_bp.login_page'))
    
    user = session['user_in_session']
    task = Task.query.get_or_404(task_id)
    
    return render_template('task_detail.html', 
                         title=task.task_name, 
                         user=user, 
                         menu=logged_user_menu(), 
                         task=task,
                         output=None)


@routes_bp.route('/compile', methods=['POST'])
def compile_file():
    if 'user_in_session' not in session:
        flash('User is not authorized')
        return redirect(url_for('routes_bp.login_page'))
    
    current_user = session['user_in_session']
    task_id = request.form.get('task_id')
    
    task = Task.query.get_or_404(task_id)
    
    TIME_LIMIT_USER = float(task.time_limit)
    TIME_LIMIT_REAL = TIME_LIMIT_USER + 0.2
    MEMORY_LIMIT_KB = int(task.memory_limit) * 1024
    
    file = request.files.get('file')
    if not file:
        flash("No file uploaded")
        return redirect(url_for('routes_bp.task_detailed', task_id=task_id))
    
    upload_folder = "/uploads"
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    with open(filepath, 'r') as f:
        code_content = f.read()
    
    output = ""
    status = "pending"
    passed_tests = 0
    total_tests = len(task.test_cases) if task.test_cases else 0
    error_message = None
    total_time = 0
    
    try:
        compile_result = subprocess.run([
            "docker", "exec", "compiler",
            "gcc", f"/uploads/{filename}", "-o", f"/uploads/output"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        
        if compile_result.returncode != 0:
            output = "Compilation Error:\n" + compile_result.stderr
            status = "compilation_error"
            error_message = compile_result.stderr
        else:
            
            if task.test_cases:
                output += f"Running test cases (Time Limit: {TIME_LIMIT_USER}s, Memory Limit: {task.memory_limit}MB):\n"
                output += "="*70 + "\n"
                
                for i, test_case in enumerate(task.test_cases, 1):
                    test_input = test_case.get('input', '')
                    expected_output = test_case.get('output', '').strip()
                    
                    start_time = time.time()
                    try:
                        run_result = subprocess.run([
                            "docker", "exec", "-i", "compiler",
                            "sh", "-c",
                            f"ulimit -v {MEMORY_LIMIT_KB} && timeout {TIME_LIMIT_REAL}s /uploads/output"
                        ], 
                        input=test_input, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        text=True, 
                        timeout=TIME_LIMIT_REAL + 1)
                        
                        exec_time = time.time() - start_time
                        total_time += exec_time
                        
                    except subprocess.TimeoutExpired:
                        output += f"Test {i}: ✗ TIME LIMIT EXCEEDED\n"
                        output += f"  Input: {test_input or '(empty)'}\n"
                        output += f"  Time limit: {TIME_LIMIT_USER}s\n\n"
                        status = "timeout"
                        error_message = "Time limit exceeded"
                        break
                    
                    if run_result.returncode == 124:
                        output += f"Test {i}: ✗ TIME LIMIT EXCEEDED\n"
                        output += f"  Input: {test_input or '(empty)'}\n"
                        output += f"  Time limit: {TIME_LIMIT_USER}s\n\n"
                        status = "timeout"
                        error_message = "Time limit exceeded"
                        break
                    elif run_result.returncode == 137:
                        output += f"Test {i}: ✗ MEMORY LIMIT EXCEEDED\n"
                        output += f"  Input: {test_input or '(empty)'}\n"
                        output += f"  Memory limit: {task.memory_limit}MB\n\n"
                        status = "runtime_error"
                        error_message = "Memory limit exceeded"
                        break
                    elif run_result.returncode == 139:
                        output += f"Test {i}: ✗ RUNTIME ERROR (Segmentation Fault)\n"
                        output += f"  Input: {test_input or '(empty)'}\n\n"
                        status = "runtime_error"
                        error_message = "Segmentation fault"
                        break
                    elif run_result.returncode != 0:
                        output += f"Test {i}: ✗ RUNTIME ERROR\n"
                        output += f"  Input: {test_input or '(empty)'}\n"
                        output += f"  Exit code: {run_result.returncode}\n"
                        if run_result.stderr:
                            output += f"  Error: {run_result.stderr[:200]}\n"
                        output += "\n"
                        status = "runtime_error"
                        error_message = run_result.stderr or f"Exit code: {run_result.returncode}"
                        break
                    
                    if exec_time > TIME_LIMIT_USER:
                        output += f"Test {i}: ✗ TIME LIMIT EXCEEDED\n"
                        output += f"  Input: {test_input or '(empty)'}\n"
                        output += f"  Time: {exec_time:.3f}s (limit: {TIME_LIMIT_USER}s)\n\n"
                        status = "timeout"
                        error_message = "Time limit exceeded"
                        break
                    
                    actual_output = run_result.stdout.strip()
                    
                    if actual_output == expected_output:
                        output += f"Test {i}: ✓ PASSED\n"
                        output += f"  Input: {test_input or '(empty)'}\n"
                        output += f"  Expected: {expected_output}\n"
                        output += f"  Got: {actual_output}\n"
                        output += f"  Time: {exec_time:.3f}s\n\n"
                        passed_tests += 1
                    else:
                        output += f"Test {i}: ✗ WRONG ANSWER\n"
                        output += f"  Input: {test_input or '(empty)'}\n"
                        output += f"  Expected: {expected_output}\n"
                        output += f"  Got: {actual_output}\n"
                        output += f"  Time: {exec_time:.3f}s\n\n"
                
                output += "="*70 + "\n"
                output += f"Result: {passed_tests}/{total_tests} tests passed\n"
                output += f"Total Time: {total_time:.3f}s\n"
                
                if status not in ["timeout", "runtime_error", "compilation_error"]:
                    status = "accepted" if passed_tests == total_tests else "wrong_answer"
            else:
                try:
                    run_result = subprocess.run([
                        "docker", "exec", "compiler",
                        "sh", "-c",
                        f"ulimit -v {MEMORY_LIMIT_KB} && timeout {TIME_LIMIT_REAL}s /uploads/output"
                    ], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True, 
                    timeout=TIME_LIMIT_REAL + 1)
                    
                    output += "\nProgram output:\n" + run_result.stdout
                    if run_result.stderr:
                        output += "\nErrors:\n" + run_result.stderr
                    status = "completed" if run_result.returncode == 0 else "runtime_error"
                    
                except subprocess.TimeoutExpired:
                    output += "\n⚠ Time limit exceeded"
                    status = "timeout"
    
    except subprocess.TimeoutExpired:
        output = "Error: Compilation timed out"
        status = "compilation_error"
        error_message = "Compilation timeout"
    except Exception as e:
        output = f"Error: {str(e)}"
        status = "runtime_error"
        error_message = str(e)
    
    try:
        user_obj = User.query.filter_by(username=current_user).first()
        submission = Submission(
            user_id=user_obj.user_id,
            task_id=task_id,
            code=code_content,
            status=status,
            passed_tests=passed_tests,
            total_tests=total_tests,
            error_message=error_message
        )
        db.session.add(submission)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving submission: {e}")
    
    return render_template('task_detail.html', 
                         title=task.task_name, 
                         user=current_user, 
                         menu=logged_user_menu(), 
                         task=task,
                         output=output)