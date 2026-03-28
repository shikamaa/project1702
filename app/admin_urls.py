from flask import Blueprint, flash, redirect, url_for, render_template
from login import admin_required

from sqlalchemy import select

from db import db
from models import Task, Submission, User
from navigation import logged_user_menu
admin_routes = Blueprint('admin_routes', __name__, url_prefix='/admin',template_folder='../templates')

@admin_routes.route('/tasks/delete/<int:task_id>', methods=['POST'])
@admin_required
def delete_task(task_id): 
    task = db.session.get(Task, task_id)
    db.session.delete(task)
    db.session.commit()
    flash(f'Task {Task.task_id} sucessfully deleted!')
    return redirect(url_for('simple_routes.show_tasks'))

@admin_routes.get('/users')
def get_users():
    all_users = db.session.execute(select(User)).scalars().all()
    if all_users != None:
        print("Good")
        
        
        
    return render_template(
        'admin/user_management.html',
        tilte='User Management',                 
        menu = logged_user_menu()  
        )