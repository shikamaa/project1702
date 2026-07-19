from flask import render_template, request, redirect, url_for, flash, Blueprint
from werkzeug.utils import secure_filename
from navigation import logged_user_menu, unlogged_user_menu
from models import User, Submission, Task, SubmissionReview, STUDENT, ADMIN, TEACHER, UserType


from flask_login import login_required, logout_user, current_user, login_user
from login import admin_required, teacher_required

routes = Blueprint('routes', __name__, template_folder ='../templates')
teacher_bp = Blueprint('teacher_bp', __name__, url_prefix='/teacher', template_folder='../templates')
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin',template_folder='../templates')


# @admin_bp.route('/users')
# @admin_required
# def admin_users():


# @admin_bp.route('/demote_all', methods=['POST'])
# @admin_required
# def demote_all():




