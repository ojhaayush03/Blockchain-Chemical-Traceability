from flask import Blueprint, render_template, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Chemical, MovementLog, AuditLog, Organization
from app.forms import MovementForm
from app import db
from app.decorators import distributor_required

# Import blockchain client if available
try:
    from app.blockchain_client import BlockchainClient
except ImportError:
    BlockchainClient = None

distributor_bp = Blueprint('distributor_bp', __name__, url_prefix='/distributor')

@distributor_bp.route('/log-movement', methods=['GET', 'POST'])
@login_required
@distributor_required
def log_movement():
    """Route for distributors to log chemical movements"""
    form = MovementForm()
    
    # Populate recipient organization choices
    form.recipient_organization.choices = [(org.id, org.name) for org in 
                                          Organization.query.filter_by(active=True).all()]
    
    if form.validate_on_submit():
        try:
            # Find the chemical by RFID tag
            chemical = Chemical.query.filter_by(rfid_tag=form.rfid_tag.data).first()
            
            if not chemical:
                flash('Chemical with this RFID tag not found.', 'error')
                return render_template('distributor/log_movement.html', form=form)
            
            # Create new movement record
            movement = MovementLog(
                tag_id=chemical.rfid_tag,
                chemical_id=chemical.id,
                location=form.destination_location.data,
                source_location=form.source_location.data,
                timestamp=datetime.utcnow(),
                purpose=form.movement_type.data,
                status='in_transit',
                remarks=form.notes.data,
                quantity_moved=form.quantity.data,
                moved_by_user_id=current_user.id,
                source_org_id=current_user.organization_id,
                destination_org_id=form.recipient_organization.data
            )
            
            db.session.add(movement)
            
            # Update chemical's current location
            chemical.current_location = "In Transit"
            chemical.last_updated = datetime.utcnow()
            chemical.current_custodian_org_id = current_user.organization_id
            
            # Create audit log
            audit_log = AuditLog(
                action='movement_created',
                object_type='movement',
                object_id=movement.id,
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                details=f"Chemical {chemical.name} movement logged from {form.source_location.data} to {form.destination_location.data}"
            )
            db.session.add(audit_log)
            
            # Record on blockchain if enabled
            if form.confirm_accuracy.data:
                try:
                    blockchain_client = BlockchainClient()
                    tx_hash = blockchain_client.record_movement(
                        movement_id=str(movement.id),
                        chemical_id=chemical.id,
                        source=form.source_location.data,
                        destination=form.destination_location.data,
                        timestamp=datetime.utcnow().isoformat(),
                        distributor_id=current_user.organization_id
                    )
                    
                    if tx_hash:
                        movement.blockchain_recorded = True
                        flash('Movement successfully recorded on blockchain.', 'success')
                    else:
                        flash('Movement logged but blockchain recording failed. An administrator will review this.', 'warning')
                except Exception as e:
                    flash(f'Movement logged but blockchain recording failed: {str(e)}. An administrator will review this.', 'warning')
            
            db.session.commit()
            flash('Chemical movement successfully logged.', 'success')
            return redirect(url_for('dashboard_bp.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error logging movement: {str(e)}', 'error')
    
    return render_template('distributor/log_movement.html', form=form)

@distributor_bp.route('/movements', methods=['GET'])
@login_required
@distributor_required
def view_movements():
    """Route for distributors to view their logged movements"""
    movements = MovementLog.query.filter_by(moved_by_user_id=current_user.id).order_by(MovementLog.timestamp.desc()).all()
    return render_template('distributor/movements.html', movements=movements)

@distributor_bp.route('/api/chemical/rfid/<rfid_tag>', methods=['GET'])
@login_required
@distributor_required
def get_chemical_by_rfid(rfid_tag):
    """API endpoint to get chemical info by RFID tag"""
    chemical = Chemical.query.filter_by(rfid_tag=rfid_tag).first()
    
    if not chemical:
        return jsonify({'error': 'Chemical not found'}), 404
    
    return jsonify({
        'id': chemical.id,
        'name': chemical.name,
        'chemical_formula': chemical.chemical_formula,
        'batch_number': chemical.batch_number,
        'current_location': chemical.current_location,
        'unit': chemical.unit
    })
