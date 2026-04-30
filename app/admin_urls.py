from flask import Blueprint, flash, redirect, url_for, render_template, request
from login import admin_required

from sqlalchemy import select, update

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
    users = db.session.execute(select(User)).scalars().all()
    fields = ["User ID", "Username", "First name", "Last name", "Role", "Registration date"]
    
    return render_template(
        'admin/user_management.html',
        title='User Management',                 
        menu = logged_user_menu(),
        columns = fields,
        users = users,
    )

@admin_routes.post("/users/<int:u_id>/change_role/<string:role>")
def change_user_role(u_id, role):
    stmt = update(User).where(User.user_id == u_id).values(user_role = role)
    db.session.execute(stmt)
    db.session.commit()

    return redirect(url_for("admin_routes.get_users"))