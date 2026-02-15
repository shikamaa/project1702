from flask import render_template, request, redirect, url_for, flash, Blueprint, current_app
import os
import subprocess
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from nav import logged_user_menu, unlogged_user_menu
from models import User, Submission, Task, STUDENT, ADMIN, TEACHER, UserType
from database1702 import db
import time
from flask_login import login_required, logout_user, current_user, login_user
from decorators import admin_required, teacher_required
import uuid

routes = Blueprint('routes', __name__, template_folder ='../template')
teacher_bp = Blueprint('teacher_bp', __name__, url_prefix='/teacher', template_folder='../templates')
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin',template_folder='../templates')


@teacher_bp.route('/student_submissions')
@teacher_required
def return_submissions():
    submissions = Submission.query \
        .join(User) \
        .filter(User.user_role == STUDENT) \
        .order_by(Submission.submitted_at.desc()) \
        .all()
    
    return render_template('all_submissions.html', 
                           submissions=submissions)

@teacher_bp.route('/add_task')
@teacher_required
def add_task():
    return render_template('add_task.html', menu=logged_user_menu())

@admin_bp.route('/approve_task/<int:task_id>', methods=['POST'])
@admin_required
def approve_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.status = True
    db.session.commit()
    flash(f'Task "{task.task_name}" approved!')
    return redirect(url_for('admin_bp.admin_tasks'))

@admin_bp.route('/reject_task/<int:task_id>', methods=['POST'])
@admin_required
def reject_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash(f'Task "{task.task_name}" rejected!')
    return redirect(url_for('admin_bp.admin_tasks'))

@admin_bp.route('/accept_task')
@admin_required
def admin_tasks():
    tasks_to_accept = Task.query.filter_by(status=False).all()
    
    return render_template('admin/accept_tasks.html', 
                         title='Admin task manager',
                         menu=logged_user_menu(),
                         tasks_to_accept=tasks_to_accept)

@admin_bp.route('/users')
@admin_required
def admin_users():
    all_users = User.query.order_by(User.user_role, User.username).all()
    return render_template('admin/users.html',
                         title='User Management',
                         menu=logged_user_menu(),
                         users=all_users)

@admin_bp.route('/demote_all', methods=['POST'])
@admin_required
def demote_all():
    demote_count = User.query.filter(
        User.username != current_user.username 
    ).update({'user_role': STUDENT})
    
    db.session.commit()
    flash(f'Demoted {demote_count} users to STUDENT role.')
    return redirect(url_for('admin_bp.admin_users'))

@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@admin_required
def change_user_role(user_id):
    user = User.query.get_or_404(user_id)

    if user.user_id == current_user.user_id:
        flash("You cannot change your own role.")
        return redirect(url_for('admin_bp.admin_users'))

    new_role = request.form.get('role')

    try:
        user.user_role = UserType[new_role]
        db.session.commit()
        flash(f"Role updated for {user.username}")
    except KeyError:
        flash("Invalid role.")

    return redirect(url_for('admin_bp.admin_users'))


@routes.route('/user_submissions')
@teacher_required
def user_submissions():
    submissions = Submission.query.filter_by(
        user_id=current_user.user_id
    ).order_by(
        Submission.submitted_at.desc()
    ).all()

    return render_template('user_submissions.html',
                         title='My Submissions',
                         menu=logged_user_menu(),
                         submissions=submissions)

@routes.route('/submission/<int:submission_id>')
@login_required
def submission_detail(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    
    if submission.user_id != current_user.user_id and \
       current_user.user_role not in (TEACHER, ADMIN):
        flash("Access denied")
        return redirect(url_for('routes.tasks'))
    
    return render_template('submission_detail.html',
                         title=f'Submission #{submission_id}',
                         menu=logged_user_menu(),
                         submission=submission)

@routes.route('/')
def main_page():
    if current_user.is_authenticated:
        return redirect(url_for('routes.tasks'))
    return render_template('login.html', 
                         title='1702 Main page',
                         menu=unlogged_user_menu())

@routes.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if current_user.is_authenticated:
        return redirect(url_for('routes.tasks'))
    
    if request.method == 'POST':
        name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('User already exists')
            return render_template('signup.html', 
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

    return render_template('signup.html', 
                         title='Signup Page',
                         menu=unlogged_user_menu())

@routes.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('routes.tasks'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('routes.tasks'))
        
        flash('Incorrect username or password')

    return render_template('login.html', 
                         title='Login page',
                         menu=unlogged_user_menu())

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login_page'))

@routes.route('/settings', methods=['GET', 'POST'])
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
                return redirect(url_for('routes.login_page'))
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

    return render_template('settings.html', 
                         title='Settings',
                         menu=logged_user_menu())

@routes.route('/tasks')
@login_required
def tasks():
    all_available_tasks = Task.query.filter_by(status='t').all()
    return render_template('tasks.html', 
                         title='Main page',
                         menu=logged_user_menu(), 
                         tasks=all_available_tasks)

@routes.route('/tasks/<int:task_id>')
@login_required
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template('task_detail.html',
                          title=task.task_name,
                          menu=logged_user_menu(),
                          task=task,
                          output=None)
    
@routes.route('/compile', methods=['POST'])
@login_required
def compile_file():
    task_id = request.form.get('task_id')
    task = Task.query.get_or_404(task_id)
    file = request.files.get('file')

    if not file:
        flash("No file uploaded")
        return redirect(url_for('routes.task_detail', task_id=task_id))

    try:
        code_content = file.read().decode('utf-8') 
    except UnicodeDecodeError:
        flash("File must be a valid text file (UTF-8).")
        return redirect(url_for('routes.task_detail', task_id=task_id))

    INTERNAL_UPLOAD_DIR = "/uploads"
    host_project_path = os.environ.get('HOST_PROJECT_PATH', os.getcwd())
    HOST_UPLOAD_DIR_FOR_DOCKER = os.path.join(host_project_path, "uploads")
    
    os.makedirs(INTERNAL_UPLOAD_DIR, exist_ok=True)
    
    unique_id = uuid.uuid4().hex
    filename_c = f"{unique_id}.c"
    filename_exe = f"{unique_id}"
    internal_file_path = os.path.join(INTERNAL_UPLOAD_DIR, filename_c)
    
    with open(internal_file_path, 'w', encoding='utf-8') as f:
        f.write(code_content)

    status = "pending"
    output_log = ""
    passed_tests = 0
    total_tests = len(task.test_cases)
    error_message_db = None
    container_id = None

    TIME_LIMIT = float(task.time_limit)
    MEMORY_LIMIT_MB = int(task.memory_limit)

    try:
        start_cmd = [
            "docker", "run", "-d", "--rm",
            "--network", "none",
            "--cpus", "0.5",
            "--memory", "128m",
            "-v", f"{HOST_UPLOAD_DIR_FOR_DOCKER}:/app",
            "-w", "/app",
            "gcc:latest",
            "sleep", "60"
        ]
        
        res = subprocess.run(start_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise Exception(f"Docker start failed: {res.stderr}")
        
        container_id = res.stdout.strip()
        compile_cmd = [
            "docker", "exec", container_id,
            "gcc", filename_c, "-o", filename_exe, "-lm", "-O2"
        ]
        cmp_res = subprocess.run(compile_cmd, capture_output=True, text=True)

        if cmp_res.returncode != 0:
            status = "compilation_error"
            clean_err = cmp_res.stderr.replace(filename_c, "source.c")
            output_log = f"Compilation Error:\n{clean_err}"
            error_message_db = "Compilation failed"
        else:
            output_log += "Compilation success.\n"
            
            for i, test in enumerate(task.test_cases, 1):
                inp = test.get('input', '')
                exp = test.get('output', '').strip()
                
                mem_kb = MEMORY_LIMIT_MB * 1024
                run_cmd_str = f"ulimit -v {mem_kb}; timeout {TIME_LIMIT}s ./{filename_exe}"
                
                t_start = time.time()
                run_res = subprocess.run(
                    ["docker", "exec", "-i", container_id, "sh", "-c", run_cmd_str],
                    input=inp, capture_output=True, text=True, timeout=TIME_LIMIT + 2
                )
                duration = time.time() - t_start
                
                actual = run_res.stdout.strip()
                exit_code = run_res.returncode
                
                verdict = "OK"
                if exit_code == 124:
                    verdict = "TL"
                    status = "timeout"
                    error_message_db = "Time Limit Exceeded"
                elif exit_code == 139:
                    verdict = "RE (SegFault)"
                    status = "runtime_error"
                    error_message_db = "Segmentation Fault"
                elif exit_code != 0:
                    verdict = f"RE ({exit_code})"
                    status = "runtime_error"
                    error_message_db = f"Runtime Error {exit_code}"
                elif actual != exp:
                    verdict = "WA"
                    if status == "pending":
                        status = "wrong_answer"
                        error_message_db = "Wrong Answer"
                else:
                    passed_tests += 1
                
                output_log += f"Test {i}: {verdict} ({duration:.3f}s)\n"
                if verdict != "OK" and verdict != "WA":
                     output_log += f" Error info: {run_res.stderr}\n"
                if verdict == "WA":
                     output_log += f" Expected: {exp}\n Got: {actual}\n"

            if status == "pending":
                status = "accepted"

    except Exception as e:
        status = "system_error"
        output_log += f"\nSystem Error: {str(e)}"
        error_message_db = "System Error"
        print(f"ERROR: {e}")

    finally:
        if os.path.exists(internal_file_path):
            try: os.remove(internal_file_path)
            except: pass
        if container_id:
            subprocess.run(["docker", "rm", "-f", container_id], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    submission = Submission(
        user_id=current_user.user_id, 
        task_id=task_id,
        code=code_content, 
        status=status,
        passed_tests=passed_tests,
        total_tests=total_tests,
        error_message=error_message_db
    )
    db.session.add(submission)
    db.session.commit()

    return render_template('task_detail.html', 
                           title=task.task_name,
                           menu=logged_user_menu(),
                           task=task, 
                           output=output_log)