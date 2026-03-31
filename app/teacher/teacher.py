from sqlalchemy import select
from flask import render_template, redirect, url_for, request, flash, Blueprint

import json
from db import db
from navigation import logged_user_menu
from login import teacher_required
from models import User, Task, Submission,SubmissionReview, STUDENT, ADMIN, STUDENT
from flask_login import current_user

teacher_urls = Blueprint('teacher_urls',  __name__, template_folder='../teacher/templates/')

@teacher_urls.route('/student_submissions')
@teacher_required
def all_submissions():
    # all_submissions = Submission.query \
    #     .join(User) \
    #     .filter(User.user_role == STUDENT) \
    #     .order_by(Submission.submitted_at.desc()) \
    #     .all()
    query  = (
        select(Submission).
        join(User, User.user_role == STUDENT).
        order_by(Submission.submitted_at.desc())
        
    )
    all_submissions = db.session.execute(query).scalars().all()
    
    
    return render_template(
        'submissions.html',
        title="Student submissions",
        data = all_submissions, 
        menu=logged_user_menu()
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

            is_active = True if current_user.user_role == ADMIN else False

            new_task = Task(
                task_name=task_name,
                task_description=task_description,
                test_cases=test_cases,
                hidden_test_cases=hidden_test_cases,
                memory_limit=memory_limit,
                time_limit=time_limit,
                status=is_active
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
            print(f"Database error: {e}")
            flash('Database error', 'error')

    return render_template('propose_task.html', menu=logged_user_menu())

@teacher_urls.route('/submission/<int:submission_id>/review', methods=['POST'])
@teacher_required
def review_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    submission.status = request.form.get('status')
    submission.comment = request.form.get('comment')

    review = SubmissionReview.query.filter_by(
        submission_id=submission_id,
        teacher_id=current_user.user_id
    ).first()

    if review:
        review.comment = request.form.get('comment')
        review.reviewed_at = db.func.now()
    else:
        review = SubmissionReview(
            submission_id=submission_id,
            teacher_id=current_user.user_id,
            comment=request.form.get('comment')
        )
        db.session.add(review)

    db.session.commit()
    flash('Review saved.')
    return redirect(url_for('teacher_urls.all_submissions'))



