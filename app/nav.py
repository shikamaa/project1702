def unlogged_user_menu():
    return [
        {"name": "Signup", "url": "routes_bp.signup_page"},
        {"name": "Login", "url": "routes_bp.login_page"}
    ]

def logged_user_menu():
    return [
        {"name": "Tasks", "url": "routes_bp.tasks"},
        {"name": "Settings", "url": "routes_bp.settings"},
        {"name": "Logout", "url": "routes_bp.logout"}
    ]