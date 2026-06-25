from datetime import datetime
from db import db
from sqlalchemy import Enum as SAEnum
import enum
from flask_login import UserMixin

class UserType(enum.Enum):
    ADMIN = 'ADMIN'
    STUDENT = 'STUDENT'
    TEACHER = 'TEACHER'
    BANNED = 'BANNED'
    
ADMIN = UserType.ADMIN
TEACHER = UserType.TEACHER
STUDENT = UserType.STUDENT

class SubmissionStatus(enum.Enum):
    REVIEWED = 'Reviewed'
    PENDING = 'Pending'
    OK = 'OK'
    COMPILATION_ERROR = 'Compilation Error'
    RUNTIME_ERROR = 'Runtime Error'
    TIME_LIMIT = 'Time Limit'
    WALL_TIME_LIMIT = 'Wall Time Limit'
    MEMORY_LIMIT = 'Memory Limit'
    WRONG_ANSWER = 'Wrong Answer'
    PRESENTATION_ERROR = 'Presentation Error'
    CHECK_FAILED = 'Check Failed'
    PARTIAL_SOLUTION = 'Partial Solution'
    SECURITY_VIOLATION = 'Security Violation'

    PENDING_CHECK = 'Pending Check'
    PENDING_REVIEW = 'Pending Review'
    ACCEPTED_TESTING = 'Accepted Testing'
    IGNORED = 'Ignored'
    DISQUALIFIED = 'Disqualified'
    REJECTED = 'Rejected'
    SUMMONED_DEFENCE = 'Summoned Defence'
    STYLE_VIOLATION = 'Style Violation'
    NO_CHANGE = 'No Change'
    REJUDGE = 'Rejudge'
    FULL_REJUDGE = 'Full Rejudge'

class User(db.Model, UserMixin):
    __tablename__ = 'usrs'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), default=None)
    password_hash = db.Column(db.Text, nullable=False)
    user_role = db.Column(SAEnum(UserType, native_enum=False), nullable=False, default=UserType.STUDENT)
    reg_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    def __init__(self, username, password_hash, first_name, last_name, user_role=STUDENT):
        self.username = username
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.user_role = user_role
        
    def get_id(self):
        return str(self.user_id)
    
    @property
    def is_active(self):
        return self.user_role != UserType.BANNED  
        
class Task(db.Model):
    __tablename__ = 'tasks'
    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(200), unique=True, nullable=False)
    task_description = db.Column(db.Text)
    test_cases = db.Column(db.JSON, nullable=False)
    hidden_test_cases = db.Column(db.JSON)
    memory_limit = db.Column(db.Integer, nullable=False, default=128)
    time_limit = db.Column(db.Integer, nullable=False, default=2)
    is_active = db.Column(db.Boolean, default=False)
    submissions = db.relationship('Submission', backref='tasks_ref', 
                                  cascade='all, delete-orphan',
                                  foreign_keys='Submission.task_id')
    
    def __repr__(self):
        return f'<Task {self.task_id}: {self.task_name}>'

class Submission(db.Model):
    __tablename__ = 'submissions'
    submission_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('usrs.user_id'), nullable=False)
    task_id = db.Column(db.BigInteger, db.ForeignKey('tasks.task_id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    status = db.Column(SAEnum(SubmissionStatus, native_enum=False), nullable=False, default=SubmissionStatus.PENDING)
    passed_tests = db.Column(db.Integer, nullable=False, default=0)
    total_tests = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, default='None') 
    comment = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    celery_task_id = db.Column(db.String(64),nullable=False)
    user_id_rel = db.relationship('User', foreign_keys=[user_id])
    task = db.relationship('Task', foreign_keys=[task_id], overlaps="submissions,tasks_ref")
    
    def __repr__(self):
        return f'<Submission {self.submission_id}>'
  
class SubmissionReview(db.Model):
    __tablename__ = 'submission_review'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    submission_id = db.Column(db.BigInteger, db.ForeignKey('submissions.submission_id'), nullable=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('usrs.user_id'), nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    comment = db.Column(db.Text)
    submission = db.relationship('Submission', backref='reviews')
    teacher = db.relationship('User', foreign_keys=[teacher_id])

