from sqlalchemy import select
from flask import render_template, redirect, url_for, request, flash, Blueprint, abort
import json
from db import db
from utils.navigation import logged_user_menu
from utils.permissions import teacher_required
from models import User, Task, Submission, SubmissionStatus
from flask_login import current_user
import logging

teacher_urls = Blueprint('teacher_urls', __name__, template_folder='templates/teacher/')

logger = logging.getLogger(__name__)

TEACHER_ALLOWED_STATUSES = {
    SubmissionStatus.OK,
    SubmissionStatus.REJECTED,
    SubmissionStatus.REVIEWED,
    SubmissionStatus.IGNORED,
}


@teacher_urls.post('/submission/<int:submission_id>/status')
@teacher_required
def change_submission_status(submission_id: int):
    try:
        status = SubmissionStatus(request.form.get('status'))
    except ValueError:
        abort(400)
    if status not in TEACHER_ALLOWED_STATUSES:
        abort(400)

    current_submission = db.session.get(Submission, submission_id)
    if current_submission is None:
        flash('Submission not found')
        return redirect(url_for('teacher_urls.all_submissions'))

    current_submission.status = status
    db.session.commit()
    logger.info(f'User {current_user.username} changed status of submission '
                f'{current_submission.submission_id} to {status.name}')
    flash('Status changed successfully')
    return redirect(url_for('teacher_urls.all_submissions'))


@teacher_urls.get('/student_submissions')
@teacher_required
def all_submissions():
    query = select(
        User.username,
        Submission.submission_id,
        Submission.task_id,
        Task.task_name,
        Submission.status,
        Submission.passed_tests,
        Submission.total_tests,
        Submission.submitted_at
    ).join(User, User.user_id == Submission.user_id)\
    .join(Task, Task.task_id == Submission.task_id)\
    .order_by(User.user_id)

    all_submissions = db.session.execute(query).all()

    return render_template(
        'submissions.html',
        title="Student submissions",
        data=all_submissions,
        menu=logged_user_menu(),
        columns=['Username', 'Task Name', 'Status', 'Tests', 'Submitted at', 'Details', 'Set status'],
        submissions=all_submissions,
        status_options=[s.value for s in TEACHER_ALLOWED_STATUSES]
    )


@teacher_urls.route('/propose_task', methods=['GET', 'POST'])
@teacher_required
def propose_task():
    if request.method == 'POST':
        try:
            task_name = request.form.get('task_name')
            task_description = request.form.get('task_description')

            mem_raw = request.form.get('memory_limit')
            time_raw = request.form.get('time_limit')

            if not mem_raw or not time_raw:
                flash('Limits of time and memory required!', 'error')
                return redirect(url_for('teacher_urls.propose_task'))

            memory_limit = int(mem_raw)
            time_limit = int(time_raw)

            try:
                test_cases = json.loads(request.form.get('test_cases'))
            except (ValueError, TypeError):
                flash('JSON Error in open tests', 'error')
                return redirect(url_for('teacher_urls.propose_task'))

            hidden_raw = request.form.get('hidden_test_cases')
            hidden_test_cases = None
            if hidden_raw and hidden_raw.strip():
                try:
                    hidden_test_cases = json.loads(hidden_raw)
                except (ValueError, TypeError):
                    flash('JSON Error in hidden tests', 'error')
                    return redirect(url_for('teacher_urls.propose_task'))

            new_task = Task(
                task_name=task_name,
                task_description=task_description,
                test_cases=test_cases,
                hidden_test_cases=hidden_test_cases,
                memory_limit=memory_limit,
                time_limit=time_limit,
                is_active=False
            )

            db.session.add(new_task)
            db.session.commit()

            flash('Task created successfully!', 'success')
            return redirect(url_for('simple_routes.show_tasks'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Data error: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            logger.exception('Database error in propose_task')
            flash('Database error', 'error')

    return render_template(
        'propose_task.html',
        title='Commit task',
        menu=logged_user_menu())


@teacher_urls.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        abort(404)

    if request.method == 'POST':
        try:
            task.task_name = request.form.get('task_name')
            task.task_description = request.form.get('task_description')

            mem_raw = request.form.get('memory_limit')
            time_raw = request.form.get('time_limit')
            if not mem_raw or not time_raw:
                flash('Limits required!', 'error')
                return redirect(url_for('teacher_urls.edit_task', task_id=task_id))

            task.memory_limit = int(mem_raw)
            task.time_limit = int(time_raw)

            try:
                task.test_cases = json.loads(request.form.get('test_cases'))
            except (ValueError, TypeError):
                flash('JSON Error in open tests', 'error')
                return redirect(url_for('teacher_urls.edit_task', task_id=task_id))

            hidden_raw = request.form.get('hidden_test_cases')
            if hidden_raw and hidden_raw.strip():
                try:
                    task.hidden_test_cases = json.loads(hidden_raw)
                except (ValueError, TypeError):
                    flash('JSON Error in hidden tests', 'error')
                    return redirect(url_for('teacher_urls.edit_task', task_id=task_id))
            else:
                task.hidden_test_cases = None

            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('simple_routes.show_tasks'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template(
        'edit_task.html',
        title='Edit Task',
        task=task,
        menu=logged_user_menu()
    )