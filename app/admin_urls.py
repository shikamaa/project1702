from flask import Blueprint, flash, redirect, url_for, render_template,abort
from login import admin_required, current_user
import logging
from sqlalchemy import select, update
from db import db
from models import Task, Submission, User
from navigation import logged_user_menu

admin_routes = Blueprint('admin_routes', __name__, url_prefix='/admin',template_folder='../templates')

logger = logging.getLogger(__name__)

@admin_routes.post('/tasks/delete/<int:task_id>')
@admin_required
def delete_task(task_id: int): 
    task = db.session.get(Task, task_id)
    db.session.delete(task)
    db.session.commit()
    logger.info(f'Task {task_id} sucessfully deleted!')
    flash(f'Task {task_id} sucessfully deleted!')

    return redirect(url_for('simple_routes.show_tasks'))

@admin_routes.post('/tasks/change-status-task/<int:task_id>')
@admin_required
def change_status_task(task_id: int):
    task = db.session.get(Task, task_id)
    if task is not None:
        task.is_active = not task.is_active
        db.session.commit()
        status = 'enabled' if task.status is True else 'disabled' 
        logger.info(f'User {current_user.username} change status of the task {task_id}: {task.name} {status}')
    else:
        abort(404)

    return redirect(url_for('simple_routes.show_tasks'))

@admin_routes.get('/users')
@admin_required
def get_users():
    users = db.session.execute(select(User)).scalars().all()
    fields = ["User ID", "Username", "First name", "Last name", "Role", "Registration date"]
    
    return render_template(
        'admin/user_management.html',
        title='User Management',                 
        menu = logged_user_menu(),
        columns = fields,
        users = users
    )

@admin_routes.post("/users/<int:u_id>/change_role/<string:role>")
@admin_required
def change_user_role(user_id, role):
    selected_user = db.session.get(User, user_id)
    if selected_user is not None:
        query = (
            update(User).where(User.user_id == user_id).values(user_role = role)
        )
        db.session.execute(query)
        db.session.commit()
        logger.info(f'User {current_user.username} changed role of {selected_user.username}')
    else:
        abort(404)

    return redirect(url_for('admin_routes.get_users'))