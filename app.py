from flask import Flask, request, url_for, render_template, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

#menu = ['Tasks', 'My Submissios', 'Admin Panel', 'Settings', 'Logout']

app = Flask(__name__)
app.secret_key = '1702school'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:brikivlui@localhost/1702school'
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
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
    def change_password(self, new_password_hash):
        self.password_hash = new_password_hash

@app.route('/index')
@app.route('/idx')
@app.route('/')
def main_page():
    return render_template('login.html', title='1702 Main page')

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    error_message = None
    if request.method == 'POST':
        name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            error = 'User already exists'
            #flash(error)
            return render_template('signup.html', title='Signup Page', error=error)
            
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
        except Exception as e:
            db.session.rollback()
        session['user_in_session'] = new_user.username
        return redirect(url_for('tasks'))

    return render_template('signup.html', title='Signup Page', error=error_message)

@app.route('/tasks')
def tasks():
    if 'user_in_session' in session:
        user = session['user_in_session']
        return render_template('tasks.html', title='Main page', user=user)
    else:
        return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    error_message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash,password):
            session['user_in_session'] = user.username
            return redirect(url_for('tasks'))
        else:
            error_message = 'Incorrect username or password'
            #flash(error_message)

    return render_template('login.html', title= 'Login page', error=error_message)

@app.route('/logout')
def logout():
    session.pop('user_in_session', None)
    return render_template('login.html', title = 'Login page')

@app.route('/settings', methods = ['GET', 'POST'])
def settings():
    # if not ('user_in_session' in session):
    #     error_message = "User is not authorized!"
    #     flash(error_message)
    #     return render_template('login.html', title= 'Login page', error=error_message)
    # return render_template('settings.html', title = 'Settings')
        # if 'user_in_session' in session:
        #     return redirect(url_for('settings'))
        # else:
        #     flash(error_message)
        # return render_template('settings.html', title = 'Settings')
        if 'user_in_session' in session:
            user = session['user_in_session']
            return render_template('settings.html', title='Main page', user=user)        
        else:
            flash('User is not authorized')
            return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
