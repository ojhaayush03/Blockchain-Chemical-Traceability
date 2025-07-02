from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Organization, RoleType, AuditLog
from app.extensions import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length

auth_bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    organization = SelectField('Organization', coerce=int)
    role = SelectField('Role', choices=[
        (RoleType.MANUFACTURER.name, 'Manufacturer'),
        (RoleType.DISTRIBUTOR.name, 'Distributor'),
        (RoleType.CUSTOMER.name, 'Customer')
    ])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')
        
        # Extract domain from email
        domain = email.data.split('@')[-1]
        
        # Check if domain belongs to a registered organization
        organization = Organization.query.filter_by(email_domain=domain, active=True).first()
        if not organization:
            raise ValidationError('Your email domain is not registered with our system. Please contact your administrator.')
        
        # Check if the role selected is allowed for this organization
        role = RoleType[self.role.data]
        if role == RoleType.MANUFACTURER and not organization.can_manufacture:
            raise ValidationError('Your organization does not have manufacturer permissions.')
        elif role == RoleType.DISTRIBUTOR and not organization.can_distribute:
            raise ValidationError('Your organization does not have distributor permissions.')
        elif role == RoleType.CUSTOMER and not organization.can_receive:
            raise ValidationError('Your organization does not have customer permissions.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html', form=form)
        
        if not user.active:
            flash('Your account has been deactivated. Please contact your administrator.', 'error')
            return render_template('auth/login.html', form=form)
        
        login_user(user)
        
        # Create audit log for login
        audit = AuditLog(
            action_type='user_login',
            user_id=user.id,
            organization_id=user.organization_id,
            object_type='User',
            object_id=user.id,
            description=f'User {user.username} logged in',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            if user.is_admin:
                next_page = url_for('admin_bp.admin_dashboard')
            elif user.role == RoleType.CUSTOMER:
                next_page = url_for('customer_bp.dashboard')
            elif user.role == RoleType.DISTRIBUTOR:
                next_page = url_for('distributor_bp.dashboard')  # Redirect to distributor dashboard
            elif user.role == RoleType.MANUFACTURER:
                next_page = url_for('manufacturer_bp.dashboard')  # Redirect to manufacturer dashboard
            else:
                next_page = url_for('dashboard_bp.dashboard')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    # Create audit log for logout
    if current_user.is_authenticated:
        audit = AuditLog(
            action_type='user_logout',
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            object_type='User',
            object_id=current_user.id,
            description=f'User {current_user.username} logged out',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Extract domain from email
        email = form.email.data
        domain = email.split('@')[-1]
        
        # Find the organization by domain
        organization = Organization.query.filter_by(email_domain=domain, active=True).first()
        
        if not organization:
            flash('Your email domain is not registered with our system.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Check if the role selected is allowed for this organization
        role = RoleType[form.role.data]
        if role == RoleType.MANUFACTURER and not organization.can_manufacture:
            flash('Your organization does not have manufacturer permissions.', 'error')
            return render_template('auth/register.html', form=form)
        elif role == RoleType.DISTRIBUTOR and not organization.can_distribute:
            flash('Your organization does not have distributor permissions.', 'error')
            return render_template('auth/register.html', form=form)
        elif role == RoleType.CUSTOMER and not organization.can_receive:
            flash('Your organization does not have customer permissions.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=role,
            organization_id=organization.id,
            active=True
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Create audit log for registration
        audit = AuditLog(
            action_type='user_registration',
            user_id=user.id,
            organization_id=user.organization_id,
            object_type='User',
            object_id=user.id,
            description=f'New user {user.username} registered with role {role.name}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/profile/<username>')
@login_required
def view_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Only admins or the user themselves can view profiles
    if not current_user.is_admin and current_user.id != user.id:
        flash('You do not have permission to view this profile.', 'error')
        return redirect(url_for('dashboard_bp.dashboard'))
    
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        user = current_user
        
        # Check if current password is correct
        if not check_password_hash(user.password_hash, form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Update password
        user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        
        # Create audit log
        audit = AuditLog(
            action_type='password_change',
            user_id=user.id,
            organization_id=user.organization_id,
            object_type='User',
            object_id=user.id,
            description=f'Password changed for user {user.username}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Your password has been updated successfully.', 'success')
        return redirect(url_for('auth.view_profile', username=user.username))
    
    return render_template('auth/change_password.html', form=form)
