from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from models import ADMIN, TEACHER

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page')
            return redirect(url_for('simple_routes.login_page'))
        
        if current_user.user_role != ADMIN:
            flash('Access denied. Admin rights required.')
            return redirect(url_for('simple_routes.show_tasks'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page')
            return redirect(url_for('simple_routes.login_page'))
        
        if current_user.user_role not in (TEACHER, ADMIN):
            flash('Access denied. Teacher or Admin rights required.')
            return redirect(url_for('simple_routes.show_tasks'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page')
                return redirect(url_for('simple_routes.login_page'))
            
            # if current_user.user_role not in roles:
            #     flash('Access denied.')
            #     return redirect(url_for('simple_routes.show_tasks'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return wrapper