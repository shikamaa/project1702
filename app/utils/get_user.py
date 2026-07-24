from flask_login import current_user
from flask_limiter.util import get_remote_address

def get_user_or_ip():
    if current_user.is_authenticated:
        return f"{current_user.user_id}"
    
    return get_remote_address()