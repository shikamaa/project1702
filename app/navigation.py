from flask import session
from models import User, STUDENT, TEACHER, ADMIN
from flask_login import current_user
from login import role_required

TEACHER_MENU = (
            {"name": "Tasks", "url": "simple_routes.show_tasks"},
            {"name": "My Submissions", "url": "simple_routes.user_submissions"},
            {"name": "All Submissions", "url": "teacher_urls.all_submissions"},
            {"name": "Add Task", "url": "teacher_urls.add_task"}, 
            {"name": "Settings", "url": "simple_routes.settings"},           
            {"name": "Logout", "url": "simple_routes.logout"}
)

ADMIN_MENU = (
    {"name": "Tasks", "url": "simple_routes.show_tasks"},
    {"name": "My Submissions", "url": "simple_routes.user_submissions"},
    {"name": "All Submissions", "url": "teacher_urls.all_submissions"},
    # {"name": "Accept Tasks", "url": "admin_bp.admin_tasks"},
    {"name": "Add Task", "url": "teacher_urls.add_task"},
    {"name": "Users", "url": "admin_routes.get_users"},
    {"name": "Settings", "url": "simple_routes.settings"},
    {"name": "Logout", "url": "simple_routes.logout"}
)

def unlogged_user_menu():
    return (
        {"name": "Login", "url": "simple_routes.login_page"},
        {"name": "Sign Up", "url": "simple_routes.signup_page"}
    )
    
def logged_user_menu():
    if current_user.user_role == STUDENT:
        menu = (
            {"name": "Tasks", "url": "simple_routes.show_tasks"},
            {"name": "My Submissions", "url": "simple_routes.user_submissions"},
            {"name": "Settings", "url": "simple_routes.settings"},
            {"name": "Logout", "url": "simple_routes.logout"}
        )
    elif current_user.user_role == TEACHER:
        menu = TEACHER_MENU
    
    elif current_user.user_role == ADMIN:
        menu = ADMIN_MENU
    return menu