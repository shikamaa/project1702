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
import redis
from functions import parse_time_output
load_dotenv()

routes = Blueprint('routes', __name__, template_folder ='../templates')
teacher_bp = Blueprint('teacher_bp', __name__, url_prefix='/teacher', template_folder='../templates')
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin',template_folder='../templates')



# @admin_bp.route('/approve_task/<int:task_id>', methods=['POST'])
# @admin_required
# def approve_task(task_id):


# @admin_bp.route('/reject_task/<int:task_id>', methods=['POST'])
# @admin_required
# def reject_task(task_id):


# @admin_bp.route('/accept_task')
# @admin_required
# def admin_tasks():


# @admin_bp.route('/users')
# @admin_required
# def admin_users():


# @admin_bp.route('/demote_all', methods=['POST'])
# @admin_required
# def demote_all():

# @admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
# @admin_required
# def change_user_role(user_id):



