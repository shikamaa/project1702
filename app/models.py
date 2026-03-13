from datetime import datetime
from db import db
from sqlalchemy import Enum
import enum
from flask_login import UserMixin

class UserType(enum.Enum):
    ADMIN = 'ADMIN'
    STUDENT = 'STUDENT'
    TEACHER = 'TEACHER'

ADMIN = UserType.ADMIN
TEACHER = UserType.TEACHER
STUDENT = UserType.STUDENT

class User(db.Model, UserMixin):
    __tablename__ = 'user_table'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    user_role = db.Column(Enum(UserType), nullable=False, default=UserType.STUDENT)
    reg_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    def __init__(self, username, password_hash, first_name, last_name, user_role=UserType.STUDENT):
        self.username = username
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.user_role = user_role
        
    def get_id(self):
        return str(self.user_id)
        
class Task(db.Model):
    __tablename__ = 'task'
    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(200), unique=True, nullable=False)
    task_description = db.Column(db.Text)
    test_cases = db.Column(db.JSON, nullable=False)
    hidden_test_cases = db.Column(db.JSON)
    memory_limit = db.Column(db.Integer, nullable=False, default=128)
    time_limit = db.Column(db.Integer, nullable=False, default=2)
    status = db.Column(db.Boolean, default=False)
    
    submissions = db.relationship('Submission', backref='task_ref', 
                                  cascade='all, delete-orphan',
                                  foreign_keys='Submission.task_id')
    
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
    error_message = db.Column(db.Text, default='None') 
    comment = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    
    user = db.relationship('User', foreign_keys=[user_id])
    #task = db.relationship('Task', foreign_keys=[task_id])
    
    def __repr__(self):
        return f'<Submission {self.submission_id}>'
    
class SubmissionReview(db.Model):
    __tablename__ = 'submission_review'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    submission_id = db.Column(db.BigInteger, db.ForeignKey('submission.submission_id'), nullable=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('user_table.user_id'), nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    comment = db.Column(db.Text)

    submission = db.relationship('Submission', backref='reviews')
    teacher = db.relationship('User', foreign_keys=[teacher_id])