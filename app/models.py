from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from database1702 import db

class User(db.Model):
    __tablename__ = 'user_table'

    user_id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, username, password_hash, first_name, last_name, is_admin=0):
        self.username = username
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin


class Task(db.Model):
    __tablename__ = 'task'

    task_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(200), unique=True, nullable=False)
    task_description = db.Column(db.Text)
    test_cases = db.Column(db.JSON, nullable=False)
    memory_limit = db.Column(db.Integer, nullable=False, default=128)
    time_limit = db.Column(db.Integer, nullable=False, default=2)

    def __repr__(self):
        return f'<Task {self.task_id}: {self.task_name}>'


class Submission(db.Model):
    __tablename__ = 'submission'

    submission_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user_table.user_id'), nullable=False)
    task_id = db.Column(db.BigInteger, db.ForeignKey('task.task_id'), nullable=False)
    
    code = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    passed_tests = db.Column(db.Integer, nullable=False, default=0)
    total_tests = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    def __repr__(self):
        return f'<Submission {self.submission_id}>'
