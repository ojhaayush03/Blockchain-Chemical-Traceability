import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from app.models import Chemical, MovementLog, AuditLog, Organization
from app.forms import ChemicalRegistrationForm, ShipmentForm
from app import db
from app.decorators import manufacturer_required
import logging
import uuid

logger = logging.getLogger(__name__)

# Import blockchain client if available
try:
    from app.blockchain_client import BlockchainClient
except ImportError:
    BlockchainClient = None

manufacturer_bp = Blueprint('manufacturer_bp', __name__, url_prefix='/manufacturer')

@manufacturer_bp.route('/dashboard')
@login_required
@manufacturer_required
def dashboard():
    """Manufacturer dashboard showing registered chemicals and shipments"""
    # Get all chemicals registered by this manufacturer
    chemicals = Chemical.query.filter_by(
        manufacturer_org_id=current_user.organization_id
    ).order_by(Chemical.created_at.desc()).all()
    
    # Get recent shipments (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    shipments = MovementLog.query.filter(
        MovementLog.source_org_id == current_user.organization_id,
        MovementLog.timestamp >= thirty_days_ago
    ).order_by(MovementLog.timestamp.desc()).all()
    
    # Calculate dashboard statistics
    total_chemicals = len(chemicals)
    pending_shipments = sum(1 for s in shipments if s.status == 'in_transit')
    shipped_chemicals = sum(1 for s in shipments if s.status == 'delivered')
    
    # Count active batches (unique batch numbers)
    active_batches = len(set(c.batch_number for c in chemicals if c.batch_number))
    
    stats = {
        'total_chemicals': total_chemicals,
        'pending_shipments': pending_shipments,
        'shipped_chemicals': shipped_chemicals,
        'active_batches': active_batches
    }
    
    return render_template(
        'manufacturer/dashboard.html',
        chemicals=chemicals,
        shipments=shipments,
        stats=stats
    )

@manufacturer_bp.route('/register-chemical', methods=['GET', 'POST'])
@login_required
@manufacturer_required
def register_chemical():
    """Route for manufacturers to register new chemicals"""
    # For GET requests, show the form
    if request.method == 'GET':
        form = ChemicalRegistrationForm()
        return render_template('manufacturer/register_chemical.html', form=form)
    
    # For POST requests, handle the form submission
    try:
        # Check if it's a form submission from the template or a JSON request from dashboard
        if request.content_type and 'application/json' in request.content_type:
            # Handle JSON request (from dashboard)
            data = request.get_json()
        else:
            # Handle form submission
            form = ChemicalRegistrationForm()
            
            if form.validate_on_submit():
                # Use provided RFID tag or generate a new one
                rfid_tag = form.rfid_tag.data if form.rfid_tag.data else f"RFID-{uuid.uuid4().hex[:12].upper()}"
                
                # Prepare data dictionary similar to dashboard
                data = {
                    'name': form.name.data,
                    'rfid_tag': rfid_tag,
                    'manufacturer': current_user.organization.name,
                    'quantity': form.quantity.data,
                    'unit': form.unit.data,
                    'expiry_date': form.expiry_date.data.strftime('%Y-%m-%d') if form.expiry_date.data else None,
                    'storage_condition': form.storage_condition.data,
                    'received_date': datetime.utcnow().strftime('%Y-%m-%d'),
                    'batch_number': form.batch_number.data,
                    'hazard_class': form.hazard_class.data,
                    'cas_number': form.cas_number.data,
                    'description': form.description.data,
                    'current_location': form.initial_location.data if form.initial_location.data else 'Storage'
                }
                
                # Handle additional fields not in the dashboard form
                if form.chemical_formula.data:
                    data['chemical_formula'] = form.chemical_formula.data
                    
                if form.manufacturing_date.data:
                    data['manufacturing_date'] = form.manufacturing_date.data.strftime('%Y-%m-%d')
                    
                if form.handling_instructions.data:
                    data['handling_instructions'] = form.handling_instructions.data
            else:
                # Form validation failed
                return render_template('manufacturer/register_chemical.html', form=form)
        
        # Convert date strings to datetime objects
        expiry_date = None
        received_date = None
        manufacturing_date = None
        
        if data.get('expiry_date'):
            expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
        if data.get('received_date'):
            received_date = datetime.strptime(data['received_date'], '%Y-%m-%d').date()
        if data.get('manufacturing_date'):
            manufacturing_date = datetime.strptime(data['manufacturing_date'], '%Y-%m-%d').date()
        
        # Create chemical in local database
        chemical = Chemical(
            name=data['name'],
            rfid_tag=data['rfid_tag'],
            current_location=data.get('current_location', 'Storage'),
            quantity=data.get('quantity'),
            unit=data.get('unit'),
            expiry_date=expiry_date,
            storage_condition=data.get('storage_condition'),
            received_date=received_date or datetime.utcnow(),
            batch_number=data.get('batch_number'),
            hazard_class=data.get('hazard_class'),
            cas_number=data.get('cas_number'),
            description=data.get('description'),
            registered_by_user_id=current_user.id,
            manufacturer_org_id=current_user.organization_id,
            current_custodian_org_id=current_user.organization_id
        )
        
        # Add additional fields if they exist
        if data.get('chemical_formula'):
            chemical.chemical_formula = data['chemical_formula']
            
        if manufacturing_date:
            chemical.manufacturing_date = manufacturing_date
            
        if data.get('handling_instructions'):
            chemical.handling_instructions = data['handling_instructions']
        
        # Handle MSDS document upload if provided (only for form submissions)
        if request.files and 'msds_document' in request.files and request.files['msds_document']:
            msds_file = request.files['msds_document']
            if msds_file.filename:
                # Generate a unique filename for the MSDS document
                filename = secure_filename(f"{chemical.name}_{uuid.uuid4().hex[:8]}.pdf")
                # Save the file
                msds_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'msds', filename)
                os.makedirs(os.path.dirname(msds_path), exist_ok=True)
                msds_file.save(msds_path)
                # Store the file path in the database
                chemical.msds_document_path = f"msds/{filename}"
        
        # Add to local database
        db.session.add(chemical)
        
        # Create audit log
        audit_log = AuditLog(
            action_type='chemical_registered',
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            object_type='Chemical',
            object_id=chemical.id,
            description=f"New chemical {chemical.name} registered with RFID {data['rfid_tag']}",
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        
        # Record on blockchain if client is available
        blockchain_result = None
        if hasattr(current_app, 'blockchain_client') and current_app.blockchain_client:
            try:
                # Get manufacturer name from the organization associated with the current user
                manufacturer = current_user.organization.name if current_user.organization else "Unknown Manufacturer"
                
                blockchain_result = current_app.blockchain_client.register_chemical(
                    data['rfid_tag'],
                    data['name'],
                    manufacturer
                )
            except Exception as e:
                blockchain_result = {'success': False, 'error': str(e)}
        
        db.session.commit()
        
        # For JSON requests (from dashboard), return JSON response
        if request.content_type and 'application/json' in request.content_type:
            response = {
                'message': 'Chemical registered successfully',
                'chemical_id': chemical.id
            }
            
            if blockchain_result:
                response['blockchain'] = blockchain_result
                
            return jsonify(response), 201
        
        # For form submissions, redirect to dashboard with flash message
        flash(f'Chemical {chemical.name} has been successfully registered with RFID tag {data["rfid_tag"]}.', 'success')
        return redirect(url_for('manufacturer_bp.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        if request.content_type and 'application/json' in request.content_type:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error registering chemical: {str(e)}', 'error')
            form = ChemicalRegistrationForm()
            return render_template('manufacturer/register_chemical.html', form=form)

@manufacturer_bp.route('/prepare-shipment/<int:chemical_id>', methods=['GET', 'POST'])
@login_required
@manufacturer_required
def prepare_shipment(chemical_id):
    """Prepare a chemical for shipment to distributors"""
    chemical = Chemical.query.get_or_404(chemical_id)
    
    # Security check - ensure the chemical belongs to the current user's organization
    if chemical.manufacturer_org_id != current_user.organization_id:
        flash('You do not have permission to prepare this chemical for shipment.', 'error')
        return redirect(url_for('manufacturer_bp.dashboard'))
    
    # Only chemicals in storage can be prepared for shipment
    if chemical.current_location != 'Storage':
        flash('This chemical is not available for shipment.', 'warning')
        return redirect(url_for('manufacturer_bp.dashboard'))
    
    # Get all distributor organizations
    distributors = Organization.query.filter_by(can_distribute=True, active=True).all()
    
    # Create shipment form
    form = ShipmentForm()
    
    # Create a dropdown for selecting distributor
    form.carrier.choices = [(d.id, d.name) for d in distributors]
    
    if form.validate_on_submit():
        try:
            # Get the selected distributor
            distributor_id = int(form.carrier.data)
            distributor = Organization.query.get_or_404(distributor_id)
            
            # Create movement log for the shipment
            movement = MovementLog(
                tag_id=chemical.rfid_tag,
                chemical_id=chemical.id,
                location='In Transit',
                source_location='Storage',
                timestamp=datetime.utcnow(),
                purpose='Manufacturer Shipment',
                status='in_transit',
                remarks=form.notes.data,
                quantity_moved=chemical.quantity,
                moved_by_user_id=current_user.id,
                source_org_id=current_user.organization_id,
                destination_org_id=distributor_id,
                tracking_number=form.tracking_number.data,
                carrier=form.carrier.data,
                temperature_controlled=form.temperature_controlled.data,
                min_temperature=form.min_temperature.data if form.temperature_controlled.data else None,
                max_temperature=form.max_temperature.data if form.temperature_controlled.data else None,
                special_handling=form.special_handling.data,
                handling_instructions=form.handling_instructions.data if form.special_handling.data else None
            )
            
            db.session.add(movement)
            
            # Update chemical's current location and custodian
            chemical.current_location = 'In Transit'
            chemical.last_updated = datetime.utcnow()
            
            # Create audit log
            audit_log = AuditLog(
                action_type='shipment_created',
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                object_type='MovementLog',
                object_id=movement.id,
                description=f"Chemical {chemical.name} prepared for shipment to {distributor.name}",
                ip_address=request.remote_addr
            )
            db.session.add(audit_log)
            
            # Record on blockchain if enabled
            if form.confirm_accuracy.data and BlockchainClient:
                try:
                    blockchain_client = BlockchainClient()
                    tx_hash = blockchain_client.record_movement(
                        movement_id=str(movement.id),
                        chemical_id=chemical.id,
                        source=current_user.organization.name,
                        destination=distributor.name,
                        timestamp=datetime.utcnow().isoformat(),
                        manufacturer_id=current_user.organization_id
                    )
                    
                    if tx_hash:
                        movement.blockchain_recorded = True
                        flash('Shipment successfully recorded on blockchain.', 'success')
                    else:
                        flash('Shipment prepared but blockchain recording failed. An administrator will review this.', 'warning')
                except Exception as e:
                    logger.error(f"Blockchain recording error: {str(e)}")
                    flash(f'Shipment prepared but blockchain recording failed: {str(e)}. An administrator will review this.', 'warning')
            
            db.session.commit()
            flash(f'Chemical {chemical.name} has been prepared for shipment to {distributor.name}.', 'success')
            return redirect(url_for('manufacturer_bp.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error preparing shipment: {str(e)}")
            flash(f'Error preparing shipment: {str(e)}', 'error')
    
    return render_template(
        'manufacturer/prepare_shipment.html',
        chemical=chemical,
        distributors=distributors,
        form=form
    )

@manufacturer_bp.route('/view-shipment/<int:shipment_id>')
@login_required
@manufacturer_required
def view_shipment(shipment_id):
    """View details of a specific shipment"""
    shipment = MovementLog.query.get_or_404(shipment_id)
    
    # Security check - ensure the shipment belongs to the current user's organization
    if shipment.source_org_id != current_user.organization_id:
        flash('You do not have permission to view this shipment.', 'error')
        return redirect(url_for('manufacturer_bp.dashboard'))
    
    # Get the chemical associated with this shipment
    chemical = Chemical.query.get(shipment.chemical_id) if shipment.chemical_id else None
    
    # Get the destination organization
    destination_org = Organization.query.get(shipment.destination_org_id) if shipment.destination_org_id else None
    
    # Get related audit logs
    audit_logs = AuditLog.query.filter_by(
        object_type='MovementLog',
        object_id=shipment.id
    ).order_by(AuditLog.timestamp.desc()).all()
    
    return render_template(
        'manufacturer/view_shipment.html',
        shipment=shipment,
        chemical=chemical,
        destination_org=destination_org,
        audit_logs=audit_logs
    )
