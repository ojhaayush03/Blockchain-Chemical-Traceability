from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, Organization, AuditLog, Chemical, MovementLog, BlockchainAnomaly
from app.extensions import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError
import re

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

# Form for adding/editing organizations
class OrganizationForm(FlaskForm):
    name = StringField('Organization Name', validators=[DataRequired()])
    email_domain = StringField('Email Domain', validators=[DataRequired()])
    description = TextAreaField('Description')
    can_manufacture = BooleanField('Can Manufacture')
    can_distribute = BooleanField('Can Distribute')
    can_receive = BooleanField('Can Receive')
    submit = SubmitField('Save Organization')
    
    def validate_email_domain(self, email_domain):
        # Remove any @ if user included it
        domain = email_domain.data.strip().lstrip('@')
        
        # Basic domain validation
        domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, domain):
            raise ValidationError('Invalid domain format. Please enter a valid domain (e.g., "company.com").')
        
        # Check if domain is already registered (except for the current org being edited)
        org_id = request.view_args.get('org_id')
        query = Organization.query.filter_by(email_domain=domain)
        if org_id:
            query = query.filter(Organization.id != org_id)
        
        if query.first():
            raise ValidationError('This email domain is already registered with another organization.')
        
        # Update the field to the cleaned domain
        email_domain.data = domain

# Admin access decorator
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard_bp.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/')
@admin_required
def admin_dashboard():
    organizations = Organization.query.all()
    users = User.query.all()
    total_chemicals = Chemical.query.count()
    total_movements = MovementLog.query.count()
    anomaly_count = BlockchainAnomaly.query.count()
    
    return render_template('admin/dashboard.html', 
                          organizations=organizations,
                          users=users,
                          total_chemicals=total_chemicals,
                          total_movements=total_movements,
                          anomaly_count=anomaly_count)

@admin_bp.route('/organizations')
@admin_required
def organization_list():
    organizations = Organization.query.all()
    return render_template('admin/organizations.html', organizations=organizations)

@admin_bp.route('/organizations/add', methods=['GET', 'POST'])
@admin_required
def add_organization():
    form = OrganizationForm()
    
    if form.validate_on_submit():
        # Create new organization
        organization = Organization(
            name=form.name.data,
            email_domain=form.email_domain.data,
            description=form.description.data,
            can_manufacture=form.can_manufacture.data,
            can_distribute=form.can_distribute.data,
            can_receive=form.can_receive.data,
            active=True
        )
        
        db.session.add(organization)
        db.session.commit()
        
        # Create audit log
        audit = AuditLog(
            action_type='organization_creation',
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            object_type='Organization',
            object_id=organization.id,
            description=f'Organization {organization.name} created with domain {organization.email_domain}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f'Organization {organization.name} has been added successfully.', 'success')
        return redirect(url_for('admin_bp.organization_list'))
    
    return render_template('admin/organization_form.html', form=form)

@admin_bp.route('/organizations/edit/<int:org_id>', methods=['GET', 'POST'])
@admin_required
def edit_organization(org_id):
    organization = Organization.query.get_or_404(org_id)
    form = OrganizationForm(obj=organization)
    
    if form.validate_on_submit():
        # Update organization
        organization.name = form.name.data
        organization.email_domain = form.email_domain.data
        organization.description = form.description.data
        organization.can_manufacture = form.can_manufacture.data
        organization.can_distribute = form.can_distribute.data
        organization.can_receive = form.can_receive.data
        
        db.session.commit()
        
        # Create audit log
        audit = AuditLog(
            action_type='organization_update',
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            object_type='Organization',
            object_id=organization.id,
            description=f'Organization {organization.name} updated',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f'Organization {organization.name} has been updated successfully.', 'success')
        return redirect(url_for('admin_bp.organization_list'))
    
    return render_template('admin/organization_form.html', form=form, organization=organization)

@admin_bp.route('/organizations/activate/<int:org_id>', methods=['POST'])
@admin_required
def activate_organization(org_id):
    organization = Organization.query.get_or_404(org_id)
    organization.active = True
    
    db.session.commit()
    
    # Create audit log
    audit = AuditLog(
        action_type='organization_activation',
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        object_type='Organization',
        object_id=organization.id,
        description=f'Organization {organization.name} activated',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()
    
    flash(f'Organization {organization.name} has been activated.', 'success')
    return redirect(url_for('admin_bp.organization_list'))

@admin_bp.route('/organizations/deactivate/<int:org_id>', methods=['POST'])
@admin_required
def deactivate_organization(org_id):
    organization = Organization.query.get_or_404(org_id)
    
    # Don't allow deactivating the system organization
    if organization.name == 'System':
        flash('Cannot deactivate the System organization.', 'error')
        return redirect(url_for('admin_bp.organization_list'))
    
    organization.active = False
    
    db.session.commit()
    
    # Create audit log
    audit = AuditLog(
        action_type='organization_deactivation',
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        object_type='Organization',
        object_id=organization.id,
        description=f'Organization {organization.name} deactivated',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()
    
    flash(f'Organization {organization.name} has been deactivated.', 'success')
    return redirect(url_for('admin_bp.organization_list'))

@admin_bp.route('/organizations/<int:org_id>/users')
@admin_required
def view_organization_users(org_id):
    organization = Organization.query.get_or_404(org_id)
    users = User.query.filter_by(organization_id=org_id).all()
    
    return render_template('admin/organization_users.html', organization=organization, users=users)

@admin_bp.route('/users')
@admin_required
def user_list():
    users = User.query.all()
    organizations = Organization.query.all()
    
    return render_template('admin/users.html', users=users, organizations=organizations)

@admin_bp.route('/users/activate/<int:user_id>', methods=['POST'])
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.active = True
    
    db.session.commit()
    
    # Create audit log
    audit = AuditLog(
        action_type='user_activation',
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        object_type='User',
        object_id=user.id,
        description=f'User {user.username} activated',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()
    
    flash(f'User {user.username} has been activated.', 'success')
    return redirect(url_for('admin_bp.user_list'))

@admin_bp.route('/users/deactivate/<int:user_id>', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow deactivating the admin user
    if user.is_admin:
        flash('Cannot deactivate the admin user.', 'error')
        return redirect(url_for('admin_bp.user_list'))
    
    user.active = False
    
    db.session.commit()
    
    # Create audit log
    audit = AuditLog(
        action_type='user_deactivation',
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        object_type='User',
        object_id=user.id,
        description=f'User {user.username} deactivated',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()
    
    flash(f'User {user.username} has been deactivated.', 'success')
    return redirect(url_for('admin_bp.user_list'))

@admin_bp.route('/audit-logs')
@admin_required
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('admin/audit_logs.html', logs=logs)

@admin_bp.route('/anomalies')
@admin_required
def view_anomalies():
    """View and manage blockchain anomalies"""
    # Get all anomalies, ordered by most recent first
    anomalies = BlockchainAnomaly.query.order_by(BlockchainAnomaly.detected_at.desc()).all()
    
    # Get statistics
    open_anomalies = sum(1 for a in anomalies if a.resolution_status == 'open')
    resolved_anomalies = sum(1 for a in anomalies if a.resolution_status == 'resolved')
    false_positives = sum(1 for a in anomalies if a.resolution_status == 'false_positive')
    
    # Group by type
    anomaly_types = {}
    for anomaly in anomalies:
        if anomaly.anomaly_type not in anomaly_types:
            anomaly_types[anomaly.anomaly_type] = 0
        anomaly_types[anomaly.anomaly_type] += 1
    
    return render_template('admin/anomalies.html', 
                          anomalies=anomalies,
                          open_anomalies=open_anomalies,
                          resolved_anomalies=resolved_anomalies,
                          false_positives=false_positives,
                          anomaly_types=anomaly_types)

@admin_bp.route('/anomalies/resolve/<int:anomaly_id>', methods=['POST'])
@admin_required
def resolve_anomaly(anomaly_id):
    anomaly = BlockchainAnomaly.query.get_or_404(anomaly_id)
    resolution_notes = request.form.get('resolution_notes', '')
    resolution_status = request.form.get('resolution_status', 'resolved')
    
    anomaly.resolution_status = resolution_status
    anomaly.resolution_notes = resolution_notes
    anomaly.resolved_by_id = current_user.id
    
    db.session.commit()
    
    # Create audit log
    audit = AuditLog(
        action_type='anomaly_resolution',
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        object_type='BlockchainAnomaly',
        object_id=anomaly.id,
        description=f'Anomaly {anomaly.id} resolved with status {resolution_status}',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()
    
    flash(f'Anomaly has been marked as {resolution_status}.', 'success')
    return redirect(url_for('admin_bp.view_anomalies'))
