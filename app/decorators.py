from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from app.models import RoleType

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth_bp.login'))
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard_bp.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def manufacturer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth_bp.login'))
        if not current_user.has_role(RoleType.MANUFACTURER):
            flash('You do not have permission to access this page. Manufacturer role required.', 'error')
            return redirect(url_for('dashboard_bp.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def distributor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth_bp.login'))
        if not current_user.has_role(RoleType.DISTRIBUTOR):
            flash('You do not have permission to access this page. Distributor role required.', 'error')
            return redirect(url_for('dashboard_bp.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth_bp.login'))
        if not current_user.has_role(RoleType.CUSTOMER):
            flash('You do not have permission to access this page. Customer role required.', 'error')
            return redirect(url_for('dashboard_bp.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """
    Decorator that checks if the current user has any of the specified roles.
    Usage: @role_required(RoleType.MANUFACTURER, RoleType.DISTRIBUTOR)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth_bp.login'))
            
            # Admin can access everything
            if current_user.is_admin:
                return f(*args, **kwargs)
                
            has_permission = False
            for role in roles:
                if current_user.has_role(role):
                    has_permission = True
                    break
                    
            if not has_permission:
                role_names = [role.value.capitalize() for role in roles]
                flash(f'You do not have permission to access this page. Required roles: {", ".join(role_names)}.', 'error')
                return redirect(url_for('dashboard_bp.dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator