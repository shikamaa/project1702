from flask import Flask, request, url_for, render_template, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import subprocess

menu = [
    {"name": "Tasks", "url": "tasks"},
    {"name": "Settings", "url": "settings"},
    {"name": "Logout", "url": "logout"}
]
def menu1():
    reg_menu = [
        {"name": "Tasks", "url": "tasks"},
        {"name": "Settings", "url": "settings"},
        {"name": "Signup", "url": "signup_page"},
        {"name": "Login", "url": "login_page"}
    ]
    return reg_menu
app = Flask(__name__)
app.secret_key = '1702school'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:brikivlui@db/1702school')
app.config['PERMANENT_SESSION_LIFETIME'] = 1800
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    role = db.Column(db.Integer)

    def __init__(self, username, password_hash, first_name=None, last_name=None, role=None):
        self.username = username
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.role = role

    def change_username(self, new_username):
        self.username = new_username

    def change_password(self, new_password):
        self.password_hash = generate_password_hash(new_password)


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
            return render_template('signup.html', title='Signup Page', error='User already exists')

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            first_name=name,
            last_name=last_name,
            role=0
        )
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Database error')
            return render_template('signup.html', title='Signup Page', error='Database error')

        session['user_in_session'] = new_user.username
        session.permanent = True
        return redirect(url_for('tasks'))

    return render_template('signup.html', title='Signup Page', menu=menu1())

@app.route('/tasks')
def tasks():
    if 'user_in_session' in session:
        user = session['user_in_session']
        return render_template('tasks.html', title='Main page', user=user, menu=menu)
    return redirect(url_for('login_page'))

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

    return render_template('login.html', title='Docker Login page', error=error_message, menu = menu1())

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

    return render_template('settings.html', title='Settings', user=user_in_session, menu=menu)

@app.route('/about')
def about():
    return render_template('about.html', title='About us', menu = menu)

@app.route('/compile', methods=['POST'])
def compile_file():
    if 'user_in_session' not in session:
        flash('User is not authorized')
        return redirect(url_for('login_page'))

    current_user = session['user_in_session']
    file = request.files.get('file')
    if not file:
        flash("No file uploaded")
        return redirect(url_for('tasks'))

    upload_folder = "/uploads"
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    try:
        result = subprocess.run([
            "docker", "exec", "compiler",
            "gcc", f"/uploads/{filename}", "-o", f"/uploads/output"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        output = result.stdout + result.stderr

        if result.returncode == 0:
            run_result = subprocess.run([
                "docker", "exec", "compiler", "/uploads/output"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output += "\nProgram output\n" + run_result.stdout + run_result.stderr

    except Exception as e:
        output = f"Error running compiler container: {e}"

    return render_template('tasks.html', title='Main page', user=current_user, menu=menu, output=output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
