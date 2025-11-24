from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import subprocess
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = '1702school'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:admin1702@db/1702school')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


def menu():
    return [
        {"name": "Tasks", "url": "tasks"},
        {"name": "Settings", "url": "settings"},
        {"name": "Logout", "url": "logout"}
    ]

def menu1():
    return [
        #{"name": "Tasks", "url": "tasks"},
        #{"name": "Settings", "url": "settings"},
        {"name": "Signup", "url": "signup_page"},
        {"name": "Login", "url": "login_page"}
    ]

class User(db.Model):
    __tablename__ = 'user_table'
    user_id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Integer)

    def __init__(self, username, password_hash, first_name=None, last_name=None, is_admin=None):
        self.username = username
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin

    def change_username(self, new_username):
        self.username = new_username

    def change_password(self, new_password):
        self.password_hash = generate_password_hash(new_password)

class Task(db.Model):
    __tablename__ = 'task'
    task_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(200), unique=True, nullable=False)
    task_description = db.Column(db.Text)
    test_cases = db.Column(db.JSON)

    def __repr__(self):
        return f'<Task {self.task_id}: {self.task_name}>'

class Submission(db.Model):
    __tablename__ = 'submission'
    
    submission_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user_table.user_id'), nullable=False)
    task_id = db.Column(db.BigInteger, db.ForeignKey('task.task_id'), nullable=False)
    
    code = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    passed_tests = db.Column(db.Integer, default=0)
    total_tests = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Submission {self.submission_id}>'

@app.route('/')
@app.route('/index')
@app.route('/idx')
def main_page():
    return render_template('login.html', title='Docker 1702 Main page')

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', title='Signup Page', error='User already exists', menu=menu1())

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
            return render_template('signup.html', title='Signup Page', error='Database error', menu=menu1())

        session['user_in_session'] = new_user.username
        session.permanent = True
        return redirect(url_for('tasks'))

    return render_template('signup.html', title='Signup Page', menu=menu1())

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    error_message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.permanent = True
            session['user_in_session'] = user.username
            return redirect(url_for('tasks'))
        error_message = 'Incorrect username or password'

    return render_template('login.html', title='Docker Login page', error=error_message, menu=menu1())

@app.route('/logout')
def logout():
    session.pop('user_in_session', None)
    return redirect(url_for('login_page'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_in_session' not in session:
        flash('User is not authorized')
        return redirect(url_for('login_page'))

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
                return redirect(url_for('login_page'))
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

    return render_template('settings.html', title='Settings', user=user_in_session, menu=menu())

@app.route('/tasks')
def tasks():
    if 'user_in_session' not in session:
        return redirect(url_for('login_page'))
    user = session['user_in_session']
    all_tasks = Task.query.all()
    return render_template('tasks.html', title='Main page', user=user, menu=menu(), tasks=all_tasks)


@app.route('/tasks/<int:task_id>')
def task_detailed(task_id):
    if 'user_in_session' not in session:
        return redirect(url_for('login_page'))
    
    user = session['user_in_session']
    task = Task.query.get_or_404(task_id)
    
    return render_template('task_detail.html', 
                         title=task.task_name, 
                         user=user, 
                         menu=menu(), 
                         task=task,
                         output=None)


@app.route('/compile', methods=['POST'])
def compile_file():
    if 'user_in_session' not in session:
        flash('User is not authorized')
        return redirect(url_for('login_page'))

    current_user = session['user_in_session']
    task_id = request.form.get('task_id')
    
    task = Task.query.get_or_404(task_id)
    
    file = request.files.get('file')
    if not file:
        flash("No file uploaded")
        return redirect(url_for('task_detailed', task_id=task_id))

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

    try:
        result = subprocess.run([
            "docker", "exec", "compiler",
            "gcc", f"/uploads/{filename}", "-o", f"/uploads/output"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)

        if result.returncode != 0:
            output = "Compilation Error:\n" + result.stderr
            status = "compilation_error"
            error_message = result.stderr
        else:
            output = "✓ Compilation successful\n\n"
            
            if task.test_cases:
                output += "Running test cases:\n" + "="*50 + "\n"
                
                for i, test_case in enumerate(task.test_cases, 1):
                    test_input = test_case.get('input', '')
                    expected_output = test_case.get('output', '').strip()
                    
                    run_result = subprocess.run([
                        "docker", "exec", "-i", "compiler", "/uploads/output"
                    ], input=test_input, stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE, text=True, timeout=5)
                    
                    actual_output = run_result.stdout.strip()
                    
                    if actual_output == expected_output:
                        output += f"Test {i}: ✓ PASSED\n"
                        output += f"  Input: {test_input or '(empty)'}\n"
                        output += f"  Expected: {expected_output}\n"
                        output += f"  Got: {actual_output}\n\n"
                        passed_tests += 1
                    else:
                        output += f"Test {i}: ✗ FAILED\n"
                        output += f"  Input: {test_input or '(empty)'}\n"
                        output += f"  Expected: {expected_output}\n"
                        output += f"  Got: {actual_output}\n\n"
                
                output += "="*50 + "\n"
                output += f"Result: {passed_tests}/{total_tests} tests passed\n"
                
                if passed_tests == total_tests:
                    status = "accepted"
                else:
                    status = "wrong_answer"
            else:
                run_result = subprocess.run([
                    "docker", "exec", "compiler", "/uploads/output"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                output += "\nProgram output:\n" + run_result.stdout
                if run_result.stderr:
                    output += "\nErrors:\n" + run_result.stderr
                status = "completed"

    except subprocess.TimeoutExpired:
        output = "Error: Program execution timed out (time limit exceeded)"
        status = "timeout"
        error_message = "Time limit exceeded"
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
                         menu=menu(), 
                         task=task,
                         output=output)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)