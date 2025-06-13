from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Chemical, MovementLog, Organization, RoleType
from app.decorators import manufacturer_required
from flask_login import login_required, current_user
from datetime import datetime

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Get chemicals with role-specific filtering
    if current_user.is_admin:
        # Admin sees all chemicals
        chemicals = Chemical.query.all()
    elif current_user.role == RoleType.MANUFACTURER:
        # Manufacturer sees chemicals their org manufactured
        chemicals = Chemical.query.filter_by(manufacturer_org_id=current_user.organization_id).all()
    elif current_user.role == RoleType.DISTRIBUTOR:
        # Distributor sees chemicals their org currently has custody of
        chemicals = Chemical.query.filter_by(current_custodian_org_id=current_user.organization_id).all()
    elif current_user.role == RoleType.CUSTOMER:
        # Customer sees chemicals their org has received
        chemicals = Chemical.query.filter_by(current_custodian_org_id=current_user.organization_id).all()
    else:
        chemicals = []
    
    # Get organization stats if admin
    organizations = []
    if current_user.is_admin:
        organizations = Organization.query.all()
    
    return render_template('dashboard.html', 
                           chemicals=chemicals, 
                           organizations=organizations)

@dashboard_bp.route('/chemical/<int:chemical_id>')
@login_required
def chemical_detail(chemical_id):
    chemical = Chemical.query.get_or_404(chemical_id)
    
    # Check if user has permission to view this chemical
    if not current_user.is_admin:
        if current_user.role == RoleType.MANUFACTURER:
            # Manufacturer can only see chemicals their org manufactured
            if chemical.manufacturer_org_id != current_user.organization_id:
                flash('You do not have permission to view this chemical.', 'danger')
                return redirect(url_for('dashboard_bp.dashboard'))
        elif current_user.role in [RoleType.DISTRIBUTOR, RoleType.CUSTOMER]:
            # Distributors and customers can only see chemicals their org has custody of
            if chemical.current_custodian_org_id != current_user.organization_id:
                flash('You do not have permission to view this chemical.', 'danger')
                return redirect(url_for('dashboard_bp.dashboard'))
    
    # Get movement logs for this chemical's RFID tag
    movement_logs = MovementLog.query.filter_by(tag_id=chemical.rfid_tag).order_by(MovementLog.timestamp.desc()).all()
    return render_template('chemical_detail.html', chemical=chemical, logs=movement_logs)

@dashboard_bp.route('/add_chemical', methods=['POST'])
@login_required
@manufacturer_required
def add_chemical():
    try:
        # Get form data
        name = request.form.get('name')
        rfid_tag = request.form.get('rfid_tag')
        manufacturer = request.form.get('manufacturer')
        quantity = request.form.get('quantity')
        unit = request.form.get('unit')
        expiry_date = request.form.get('expiry_date')
        storage_condition = request.form.get('storage_condition')
        received_date = request.form.get('received_date')
        batch_number = request.form.get('batch_number')
        hazard_class = request.form.get('hazard_class')
        cas_number = request.form.get('cas_number')
        description = request.form.get('description')
        current_location = request.form.get('current_location', 'Storage')
        
        # Prepare data for registration
        chemical_data = {
            'name': name,
            'rfid_tag': rfid_tag,
            'manufacturer': manufacturer,
            'quantity': float(quantity) if quantity else None,
            'unit': unit,
            'expiry_date': expiry_date,  # The register-chemical endpoint will handle date conversion
            'storage_condition': storage_condition,
            'received_date': received_date,  # The register-chemical endpoint will handle date conversion
            'batch_number': batch_number,
            'hazard_class': hazard_class,
            'cas_number': cas_number,
            'description': description,
            'current_location': current_location
        }
        
        # Use the register-chemical endpoint to handle both database and blockchain registration
        import requests
        
        # Make request to register-chemical endpoint
        response = requests.post(
            'http://localhost:5000/register-chemical',
            json=chemical_data
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to register chemical: {response.text}")
            
        # Log initial location if provided
        if 'location' in request.form and request.form.get('location'):
            new_log = MovementLog(
                tag_id=rfid_tag,
                location=request.form.get('location'),
                timestamp=datetime.utcnow(),
                status='Initial Registration'
            )
            db.session.add(new_log)
            db.session.commit()
        
        return redirect(url_for('dashboard_bp.dashboard'))
    except Exception as e:
        # Handle errors
        db.session.rollback()
        return f"Error adding chemical: {str(e)}", 500
