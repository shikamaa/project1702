from flask import session
from models import User, STUDENT, TEACHER, ADMIN
from flask_login import current_user
from decorators import role_required

TEACHER_MENU = (
            {"name": "Tasks", "url": "routes.tasks"},
            {"name": "My Submissions", "url": "routes.user_submissions"},
            {"name": "All Submissions", "url": "teacher_bp.all_submissions"},
            {"name": "Add Task", "url": "teacher_bp.add_task"}, 
            {"name": "Settings", "url": "routes.settings"},           
            {"name": "Logout", "url": "routes.logout"}
)

ADMIN_MENU = (
    {"name": "Tasks", "url": "routes.tasks"},
    {"name": "My Submissions", "url": "routes.user_submissions"},
    {"name": "All Submissions", "url": "teacher_bp.all_submissions"},
    {"name": "Accept Tasks", "url": "admin_bp.admin_tasks"},
    {"name": "Add Task", "url": "teacher_bp.add_task"},
    {"name": "Users", "url": "admin_bp.admin_users"},
    {"name": "Settings", "url": "routes.settings"},
    {"name": "Logout", "url": "routes.logout"}
)

def unlogged_user_menu():
    return (
        {"name": "Login", "url": "routes.login_page"},
        {"name": "Sign Up", "url": "routes.signup_page"}
    )
def logged_user_menu():
    if current_user.user_role == STUDENT:
        menu = (
            {"name": "Tasks", "url": "routes.tasks"},
            {"name": "My Submissions", "url": "routes.user_submissions"},
            {"name": "Settings", "url": "routes.settings"},
            {"name": "Logout", "url": "routes.logout"}
        )
    elif current_user.user_role == TEACHER:
        menu = TEACHER_MENU
    
    elif current_user.user_role == ADMIN:
        menu = ADMIN_MENU
    return menu