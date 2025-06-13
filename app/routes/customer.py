from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Chemical, MovementLog, AuditLog, CustomerReceipt
from app.forms import VerifyReceiptForm, ConfirmReceiptForm
from app import db
from app.decorators import customer_required

# Import blockchain client if available
try:
    from app.blockchain_client import BlockchainClient
except ImportError:
    BlockchainClient = None

customer_bp = Blueprint('customer_bp', __name__, url_prefix='/customer')

@customer_bp.route('/verify-receipt', methods=['GET', 'POST'])
@login_required
@customer_required
def verify_receipt():
    """Route for customers to verify chemical receipts"""
    form = VerifyReceiptForm()
    
    if form.validate_on_submit():
        # Find the movement by ID
        movement = MovementLog.query.filter_by(id=form.movement_id.data).first()
        
        if not movement:
            flash('Movement record not found. Please check the movement ID.', 'error')
            return render_template('customer/verify_receipt.html', form=form)
        
        # Check if the movement is intended for this customer's organization
        if movement.destination_org_id != current_user.organization_id:
            flash('This shipment is not intended for your organization.', 'error')
            return render_template('customer/verify_receipt.html', form=form)
        
        # Find the chemical
        chemical = Chemical.query.filter_by(id=movement.chemical_id).first()
        
        if not chemical:
            flash('Chemical record not found.', 'error')
            return render_template('customer/verify_receipt.html', form=form)
        
        # Verify RFID tag if provided
        if form.rfid_tag.data and form.rfid_tag.data != chemical.rfid_tag:
            flash('RFID tag does not match the movement record.', 'error')
            return render_template('customer/verify_receipt.html', form=form)
        
        # Verify on blockchain if enabled
        blockchain_verified = False
        blockchain_tx_hash = None
        
        try:
            blockchain_client = BlockchainClient()
            verification_result = blockchain_client.verify_movement(movement.id)
            
            if verification_result:
                blockchain_verified = True
                blockchain_tx_hash = movement.blockchain_tx_hash
        except Exception as e:
            flash(f'Blockchain verification error: {str(e)}', 'warning')
        
        # Return verification result
        return render_template(
            'customer/verify_receipt.html',
            form=form,
            movement=movement,
            chemical=chemical,
            blockchain_verified=blockchain_verified,
            blockchain_tx_hash=blockchain_tx_hash,
            verification_complete=True
        )
    
    return render_template('customer/verify_receipt.html', form=form)

@customer_bp.route('/confirm-receipt', methods=['POST'])
@login_required
@customer_required
def confirm_receipt():
    """Route for customers to confirm receipt of chemicals"""
    form = ConfirmReceiptForm()
    
    if form.validate_on_submit():
        movement_id = form.movement_id.data
        movement = MovementLog.query.filter_by(id=movement_id).first()
        
        if not movement:
            flash('Movement record not found.', 'error')
            return redirect(url_for('customer_bp.verify_receipt'))
        
        # Check if the movement is intended for this customer's organization
        if movement.destination_org_id != current_user.organization_id:
            flash('This shipment is not intended for your organization.', 'error')
            return redirect(url_for('customer_bp.verify_receipt'))
        
        # Check if already received
        receipt = CustomerReceipt.query.filter_by(movement_log_id=movement.id).first()
        if receipt:
            flash('This shipment has already been marked as received.', 'info')
            return redirect(url_for('dashboard_bp.dashboard'))
        
        # Update movement status
        movement.status = 'delivered'
        movement.received_by = current_user.id
        movement.receipt_notes = form.receipt_notes.data
        movement.quantity_confirmed = form.confirm_quantity.data
        movement.condition_confirmed = form.confirm_condition.data
        
        # Verify the RFID tag matches
        chemical = Chemical.query.filter_by(id=movement.chemical_id).first()
        if not chemical or (form.rfid_tag.data and movement.tag_id != form.rfid_tag.data):
            flash('RFID tag does not match the movement record.', 'error')
            return render_template('customer/verify_receipt.html', form=form)
        
        # Create a receipt record
        receipt = CustomerReceipt(
            movement_log_id=movement.id,
            chemical_id=chemical.id,
            received_quantity=movement.quantity_moved,
            expected_quantity=movement.quantity_moved,
            quality_check_passed=form.confirm_condition.data,
            quality_remarks=form.receipt_notes.data,
            received_by_user_id=current_user.id,
            customer_org_id=current_user.organization_id
        )
        
        # Create audit log
        audit_log = AuditLog(
            action='receipt_confirmed',
            object_type='movement',
            object_id=movement.id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            details=f"Receipt confirmed for chemical movement {movement.id}"
        )
        db.session.add(audit_log)
        db.session.add(receipt)
        
        # Record on blockchain if enabled
        try:
            blockchain_client = BlockchainClient()
            tx_hash = blockchain_client.confirm_receipt(
                movement_id=movement.id,
                recipient_id=current_user.organization_id,
                timestamp=datetime.utcnow().isoformat(),
                notes=form.receipt_notes.data
            )
            
            if tx_hash:
                movement.receipt_blockchain_tx_hash = tx_hash
                flash('Receipt confirmation successfully recorded on blockchain.', 'success')
            else:
                flash('Receipt confirmed but blockchain recording failed. An administrator will review this.', 'warning')
        except Exception as e:
            flash(f'Receipt confirmed but blockchain recording failed: {str(e)}. An administrator will review this.', 'warning')
        
        db.session.commit()
        flash('Chemical receipt successfully confirmed.', 'success')
        return redirect(url_for('dashboard_bp.dashboard'))
    
    flash('Invalid form submission.', 'error')
    return redirect(url_for('customer_bp.verify_receipt'))

@customer_bp.route('/receipts', methods=['GET'])
@login_required
@customer_required
def view_receipts():
    """Route for customers to view their received chemicals"""
    # Get movements where this organization is the recipient and status is delivered
    receipts = MovementLog.query.filter_by(
        destination_org_id=current_user.organization_id,
        status='delivered'
    ).order_by(MovementLog.timestamp.desc()).all()
    
    # Get pending receipts (in transit to this organization)
    pending = MovementLog.query.filter_by(
        destination_org_id=current_user.organization_id,
        status='in_transit'
    ).order_by(MovementLog.timestamp.desc()).all()
    
    return render_template('customer/receipts.html', receipts=receipts, pending=pending)

@customer_bp.route('/shipments/pending', methods=['GET'])
@login_required
@customer_required
def pending_shipments():
    """View pending shipments for the customer's organization"""
    pending = MovementLog.query.filter_by(
        destination_org_id=current_user.organization_id,
        status='in_transit'
    ).order_by(MovementLog.timestamp).all()
    
    return render_template('customer/receipts.html', receipts=[], pending=pending)
