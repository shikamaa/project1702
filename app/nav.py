from flask import session
from models import User, UserType

def unlogged_user_menu():
    return [
        {"name": "Login", "url": "routes_bp.login_page"},
        {"name": "Sign Up", "url": "routes_bp.signup_page"}
    ]

def logged_user_menu():
    if 'user_in_session' not in session:
        return []

    user = User.query.filter_by(
        username=session['user_in_session']
    ).first()

    if not user:
        return []

    base_menu = [
        {"name": "Tasks", "url": "routes_bp.tasks"},
        {"name": "My Submissions", "url": "routes_bp.user_submissions"},
        {"name": "Settings", "url": "routes_bp.settings"},
        {"name": "Logout", "url": "routes_bp.logout"}
    ]

    role = user.user_role.value

    if role == "teacher":
        base_menu.insert(1, {
            "name": "View Submissions",
            "url": "teacher_bp.ret_submissions"
        })

    if role == "admin":
        return [
            {"name": "Tasks", "url": "routes_bp.tasks"},
            {"name": "My Submissions", "url": "routes_bp.user_submissions"},
            {"name": "Settings", "url": "routes_bp.settings"},
            {"name": "Users", "url": "admin_bp.admin_users"},
            #{"name": "Dashboard", "url": "routes_bp.admin_dashboard"},
            #{"name": "Tasks Management", "url": "routes_bp.admin_tasks"},
            {"name": "Logout", "url": "routes_bp.logout"}
        ]

    return base_menu