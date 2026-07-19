from flask import Blueprint, flash, redirect, url_for, render_template, abort, request
from login import admin_required, current_user
import logging
from sqlalchemy import select
from db import db
from models import Task, User, UserType
from navigation import logged_user_menu

admin_routes = Blueprint('admin_routes', __name__, url_prefix='/admin', template_folder='templates/admin/')
logger = logging.getLogger(__name__)


@admin_routes.post('/tasks/delete/<int:task_id>')
@admin_required
def delete_task(task_id: int):
    current_task = db.session.get(Task, task_id)
    if current_task is not None:
        db.session.delete(current_task)
        db.session.commit()
        logger.info(f'Task {current_task.task_id} successfully deleted!')
        flash(f'Task {current_task.task_id} successfully deleted!')
    else:
        flash(f'Task {task_id} not found')
    return redirect(url_for('simple_routes.show_tasks'))


@admin_routes.post('/tasks/change-status-task/<int:task_id>')
@admin_required
def change_status_task(task_id: int):
    current_task = db.session.get(Task, task_id)
    if current_task is None:
        abort(404)
    current_task.is_active = not current_task.is_active
    db.session.commit()
    status = 'enabled' if current_task.is_active else 'disabled'
    logger.info(
        f'User {current_user.username} changed status of task '
        f'{current_task.task_id}: {current_task.task_name} -> {status}'
    )
    return redirect(url_for('simple_routes.show_tasks'))


@admin_routes.get('/users')
@admin_required
def get_users():
    users = db.session.execute(select(User)).scalars().all()
    fields = ["User ID", "Username", "First name", "Last name", "Role"]
    return render_template(
        'admin/user_management.html',
        title='User Management',
        menu=logged_user_menu(),
        columns=fields,
        users=users
    )


@admin_routes.post('/users/<int:user_id>/change-role')
@admin_required
def change_user_role(user_id: int):
    try:
        role = UserType(request.form.get('role'))
    except ValueError:
        abort(400)

    selected_user = db.session.get(User, user_id)
    if selected_user is None:
        abort(404)

    if selected_user.user_id == current_user.user_id:
        flash('You cannot change your own role')
        return redirect(url_for('admin_routes.get_users'))

    selected_user.user_role = role
    db.session.commit()
    logger.info(f'User {current_user.username} changed role of '
                f'{selected_user.username} to {role.name}')
    flash(f'Role of {selected_user.username} changed to {role.name}')
    return redirect(url_for('admin_routes.get_users'))


@admin_routes.get('/tasks/admin-panel')
@admin_required
def admin_tasks():
    query = select(Task).where(Task.is_active == False)
    tasks = db.session.execute(query).scalars().all()
    return render_template(
        'accept_tasks.html',
        title='Accept Tasks',
        menu=logged_user_menu(),
        tasks_to_accept=tasks
    )


@admin_routes.post('/tasks/approve/<int:task_id>')
@admin_required
def approve_task(task_id: int):
    task = db.session.get(Task, task_id)
    if task is None:
        abort(404)
    task.is_active = True
    db.session.commit()
    logger.info(f'Admin {current_user.username} approved task {task_id}: {task.task_name}')
    flash(f'Task "{task.task_name}" approved.')
    return redirect(url_for('admin_routes.admin_tasks'))


@admin_routes.post('/tasks/reject/<int:task_id>')
@admin_required
def reject_task(task_id: int):
    task = db.session.get(Task, task_id)
    if task is None:
        abort(404)
    task_name = task.task_name
    db.session.delete(task)
    db.session.commit()
    logger.info(f'Admin {current_user.username} rejected and deleted task {task_id}: {task_name}')
    flash(f'Task "{task_name}" rejected and removed.')
    return redirect(url_for('admin_routes.admin_tasks'))