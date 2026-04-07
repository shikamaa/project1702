from flask import render_template, request, redirect, url_for, flash, Blueprint
import os
import subprocess
from werkzeug.utils import secure_filename
from navigation import logged_user_menu, unlogged_user_menu
from models import User, Submission, Task, SubmissionReview, STUDENT, ADMIN, TEACHER, UserType

from db import db
import time
from flask_login import login_required, logout_user, current_user, login_user
from login import admin_required, teacher_required
import uuid
import json
from dotenv import load_dotenv
from sqlalchemy import select
import shutil

from functions import parse_time_output
load_dotenv()

routes = Blueprint('routes', __name__, template_folder ='../templates')
teacher_bp = Blueprint('teacher_bp', __name__, url_prefix='/teacher', template_folder='../templates')
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin',template_folder='../templates')

# @admin_bp.route('/approve_task/<int:task_id>', methods=['POST'])
# @admin_required
# def approve_task(task_id):
#     task = Task.query.get_or_404(task_id)
#     task.status = True
#     db.session.commit()
#     flash(f'Task "{task.task_name}" approved!')
#     return redirect(url_for('admin_bp.admin_tasks'))

# @admin_bp.route('/reject_task/<int:task_id>', methods=['POST'])
# @admin_required
# def reject_task(task_id):
#     # task = Task.query.get_or_404(task_id)

#     task = db.get_or_404(Task.task_id, task_id)
#     db.session.delete(task)
#     db.session.commit()
#     flash(f'Task "{task.task_name}" rejected!')
#     return redirect(url_for('admin_bp.admin_tasks'))

# @admin_bp.route('/accept_task')
# @admin_required
# def admin_tasks():
#     tasks_to_accept = Task.query.filter_by(status=False).all()
    
#     return render_template('admin/accept_tasks.html', 
#                          title='Admin task manager',
#                          menu=logged_user_menu(),
#                          tasks_to_accept=tasks_to_accept)

# @admin_bp.route('/users')
# @admin_required
# def admin_users():
#     all_users = User.query.order_by(User.user_role, User.username).all()
#     return render_template('admin/user_management.html',
#                          title='User Management',
#                          menu=logged_user_menu(),
#                          users=all_users)

# @admin_bp.route('/demote_all', methods=['POST'])
# @admin_required
# def demote_all():
#     demote_count = User.query.filter(
#         User.username != current_user.username 
#     ).update({'user_role': STUDENT})
    
#     db.session.commit()
#     flash(f'Demoted {demote_count} users to STUDENT role.')
#     return redirect(url_for('admin_bp.admin_users'))

# @admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
# @admin_required
# def change_user_role(user_id):
#     user = User.query.get_or_404(user_id)

#     if user.user_id == current_user.user_id:
#         flash("You cannot change your own role.")
#         return redirect(url_for('admin_bp.admin_users'))

#     new_role = request.form.get('role')

#     try:
#         user.user_role = UserType[new_role]
#         db.session.commit()
#         flash(f"Role updated for {user.username}")
#     except KeyError:
#         flash("Invalid role.")

#     return redirect(url_for('admin_bp.admin_users'))


load_dotenv(dotenv_path='/app/.env')

@routes.route('/compile/', methods=['GET','POST'])
@login_required
def compile_file():
    current_task = int(request.form.get('task_id'))
    task = db.session.get(Task, current_task)
    
    file = request.files.get('file')
    
    if not file or not file.filename.endswith('.c'):
        flash('Not found')
        return redirect(url_for('simple_routes.show_task_detailed'))
    
    submission_id = uuid.uuid4().hex
    
    local_dir = os.path.join(os.getenv('FILEPATH'), submission_id) 
    host_dir = os.path.join(os.getenv('HOST_UPLOADS'), submission_id)
    
    os.makedirs(local_dir, exist_ok=True)
    filepath = os.path.join(local_dir, 'solution.c')

    try:
        try:
            code_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            flash("UnicodeDecodeError")
            return redirect(url_for('simple_routes.show_task_detailed'))

        file.seek(0)
        file.save(filepath)
        
        time_limit = task.time_limit
        memory_limit = task.memory_limit
        
        open_test_cases = task.test_cases or []
        hidden_test_cases = task.hidden_test_cases or []
        
        results = []
        passed = 0
        hidden_passed = 0
        final_verdict = 'OK'

        is_compiled = subprocess.run(
            [
                'docker', 'run', '--rm',
                '--network=none',
                '-v', f'{host_dir}:/box',
                'sh', '-c',
                'gcc /box/solution.c -o /box/solution'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if is_compiled.returncode != 0:
            final_verdict = 'CE'
            flash("COMPILE ERROR")
            print("Thats CE:\n", is_compiled.stderr)
            return redirect(url_for('simple_routes.show_tasks'))
        else:
            for each_test in open_test_cases:
                inp = each_test["input"]
                expected_output = each_test["output"]
                
                try:
                    result = subprocess.run(
                        [
                            'docker', 'run', '--rm', '-i',
                            f'--memory={memory_limit}m',
                            '--cpus=0.5',
                            '--pids-limit=64',
                            '--network=none',
                            '-v', f'{host_dir}:/box',
                            'judge',
                            'sh', '-c',
                            '/usr/bin/time -v /box/solution'
                        ],
                        input=inp.encode(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=time_limit + 5
                    )
                except subprocess.TimeoutExpired:
                    final_verdict = 'TLE'
                    break

                stdout = result.stdout.decode().strip()
                stderr = result.stderr.decode()
                print(stdout, "\n", stderr)
                
                if result.returncode != 0 and 'Maximum resident set size' not in stderr:
                    verdict = 'RE'
                    final_verdict = 'RE'
                    results.append({
                        'verdict': verdict,
                        'stdout': '',
                        'stderr': stderr,
                        'memory': 0
                    })
                    break  
                
                elapsed, memory = parse_time_output(stderr)

                if elapsed > time_limit:
                    verdict = 'TLE'
                    final_verdict = 'TLE'
                elif memory > memory_limit * 1024:
                    verdict = 'MLE'
                    final_verdict = 'MLE'
                elif stdout == expected_output.strip():
                    verdict = 'OK'
                    passed += 1
                else:
                    verdict = 'WA'
                    final_verdict = 'WA'

                results.append({
                    'verdict': verdict,
                    'stdout': stdout,
                    'stderr': stderr,
                    'memory': memory
                })
                
                if verdict != 'OK':
                    break

            if final_verdict == 'OK' and hidden_test_cases:
                for each_test in hidden_test_cases:
                    inp = each_test["input"]
                    expected_output = each_test["output"]
                    
                    try:
                        result = subprocess.run(
                            [
                                'docker', 'run', '--rm', '-i',
                                f'--memory={memory_limit}m',
                                '--cpus=0.5',
                                '--pids-limit=64',
                                '--network=none',
                                '-v', f'{host_dir}:/box',
                                'judge',
                                'sh', '-c',
                                '/usr/bin/time -v /box/solution'
                            ],
                            input=inp.encode(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=time_limit + 5
                        )
                    except subprocess.TimeoutExpired:
                        final_verdict = 'TLE'
                        break

                    stdout = result.stdout.decode().strip()
                    stderr = result.stderr.decode()
                    
                    if result.returncode != 0 and 'Maximum resident set size' not in stderr:
                        final_verdict = 'RE'
                        break

                    elapsed, memory = parse_time_output(stderr)

                    if elapsed > time_limit:
                        final_verdict = 'TLE'
                        break
                    elif memory > memory_limit * 1024:
                        final_verdict = 'MLE'
                        break
                    elif stdout == expected_output.strip():
                        hidden_passed += 1
                    else:
                        final_verdict = 'WA'
                        break

        total_open = len(open_test_cases)
        total_hidden = len(hidden_test_cases)
        total_tests_count = total_open + total_hidden

        submission = Submission(
            user_id=int(current_user.get_id()),
            task_id=current_task,
            code=code_content,
            status=final_verdict,
            passed_tests=passed + hidden_passed,
            total_tests=total_tests_count,
        )
        db.session.add(submission)
        db.session.commit()
        
        return render_template(
            'task_detailed.html',
            title=f'Task {current_task}',
            menu=logged_user_menu(),
            task=task,
            output=results,
            final_verdict=final_verdict,
            passed=passed + hidden_passed,
            total=total_tests_count,
        )

    finally:
        if os.path.exists(local_dir):
            shutil.rmtree(local_dir, ignore_errors=True)