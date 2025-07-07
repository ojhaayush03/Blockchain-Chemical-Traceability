from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models import Chemical, MovementLog, AuditLog, CustomerReceipt, BlockchainAnomaly, ChemicalOrder, OrderItem
from app.forms import VerifyReceiptForm, ConfirmReceiptForm, OrderForm
from app import db
from app.decorators import customer_required
import logging
import uuid
import json

logger = logging.getLogger(__name__)

# Import blockchain client if available
try:
    from app.blockchain_client import BlockchainClient
except ImportError:
    BlockchainClient = None
    
customer_bp = Blueprint('customer_bp', __name__, url_prefix='/customer')

@customer_bp.route('/dashboard')
@login_required
@customer_required
def dashboard():
    """Customer dashboard showing orders and recent deliveries"""
    # Get all orders for this customer's organization
    orders = ChemicalOrder.query.filter_by(
        customer_org_id=current_user.organization_id
    ).order_by(ChemicalOrder.order_date.desc()).all()
    
    # Get recent deliveries (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_deliveries = MovementLog.query.filter(
        MovementLog.destination_org_id == current_user.organization_id,
        MovementLog.status == 'delivered',
        MovementLog.timestamp >= thirty_days_ago
    ).order_by(MovementLog.timestamp.desc()).all()
    
    # Calculate dashboard statistics
    total_orders = len(orders)
    pending_orders = sum(1 for order in orders if order.status in ['pending', 'approved', 'processing'])
    completed_orders = sum(1 for order in orders if order.status == 'delivered')
    pending_delivery = sum(1 for order in orders if order.status in ['approved', 'processing', 'shipped'])
    
    # Get unique chemical types ordered
    chemical_types = set()
    for order in orders:
        for item in order.items:
            chemical_types.add(item.chemical_name)
    
    # Debug information
    print(f"Found {total_orders} orders for organization ID {current_user.organization_id}")
    for order in orders:
        print(f"Order #{order.order_number}: {order.status}, {len(order.items)} items")
    
    stats = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'pending_delivery': pending_delivery,
        'completed_orders': completed_orders,
        'chemical_types': len(chemical_types)
    }
    
    return render_template(
        'customer/dashboard.html',
        orders=orders,
        recent_deliveries=recent_deliveries,
        stats=stats
    )

@customer_bp.route('/orders/place', methods=['GET', 'POST'])
@login_required
@customer_required
def place_order():
    """Route for customers to place new chemical orders"""
    logger.info("Place order route accessed by user %s (org: %s)", current_user.email, current_user.organization_id)
    form = OrderForm()
    
    # Get all available chemicals from the database
    available_chemicals = Chemical.query.all()
    logger.debug("Found %d available chemicals", len(available_chemicals))
    
    # Debug form submission
    if request.method == 'POST':
        logger.debug("POST request received with data: %s", request.form)
        logger.debug("Form errors: %s", form.errors)
        logger.debug("Form validation result: %s", form.validate())
        
        # Check specific fields
        logger.debug("items_data field: %s", form.items_data.data if hasattr(form, 'items_data') and form.items_data else "Not found")
        logger.debug("confirm_terms field: %s", form.confirm_terms.data if hasattr(form, 'confirm_terms') and form.confirm_terms else "Not found")
    
    if form.validate_on_submit():
        logger.info("Form validated successfully")
        try:
            # Generate a unique order number
            order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            logger.debug("Generated order number: %s", order_number)
            
            # Create new order
            order = ChemicalOrder(
                order_number=order_number,
                customer_id=current_user.id,
                customer_org_id=current_user.organization_id,
                order_date=datetime.utcnow(),
                required_by_date=form.required_by_date.data,  # Now correctly handled as a date
                delivery_address=form.delivery_address.data,
                special_instructions=form.special_instructions.data,
                status='pending',
                total_amount=0.0  # Will be calculated from items
            )
            
            logger.debug("Created order object: %s", order)
            db.session.add(order)
            db.session.flush()  # Get the order ID
            logger.debug("Order flushed to DB with ID: %s", order.id)
            
            # Process order items from form data
            items_data = json.loads(form.items_data.data)
            logger.debug("Parsed items_data: %s", items_data)
            total_amount = 0.0
            
            # Process order items
            for i, item_data in enumerate(items_data):
                logger.debug("Processing item %d: %s", i+1, item_data)
                # Find the chemical by ID if provided
                chemical_id = item_data.get('chemical_id')
                chemical = None
                
                if chemical_id:
                    chemical = Chemical.query.get(int(chemical_id))
                    logger.debug("Found chemical: %s", chemical)
        
                # Create order item
                item = OrderItem(
                    order_id=order.id,
                    chemical_name=item_data['chemical_name'],
                    chemical_id=chemical.id if chemical else None,
                    # Removed chemical_cas as it's not in the OrderItem model
                    quantity=float(item_data['quantity']),
                    unit=item_data['unit'],
                    unit_price=float(item_data.get('unit_price', 0.0)),
                    special_requirements=item_data.get('special_requirements', ''),
                    status='pending'
                )
                
                # Add to total amount
                item_total = item.quantity * item.unit_price
                total_amount += item_total
                
                logger.debug("Created order item: %s", item)
                db.session.add(item)
            
            # Update order total
            order.total_amount = total_amount
            logger.debug("Updated order total amount: %s", total_amount)
            
            # Create audit log
            audit_log = AuditLog(
                action_type='order_placed',
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                object_type='ChemicalOrder',
                object_id=order.id,
                description=f"New chemical order {order_number} placed with {len(items_data)} items",
                ip_address=request.remote_addr
            )
            db.session.add(audit_log)
            logger.debug("Added audit log: %s", audit_log)
            
            db.session.commit()
            logger.info("Order %s successfully committed to database", order_number)
            
            flash(f'Order {order_number} has been successfully placed and is pending approval.', 'success')
            return redirect(url_for('customer_bp.view_order', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            logger.error("Error placing order: %s", str(e), exc_info=True)
            flash(f'Error placing order: {str(e)}', 'error')
            return redirect(url_for('customer_bp.dashboard'))
    else:
        if request.method == 'POST':
            logger.warning("Form validation failed with errors: %s", form.errors)
    
    return render_template('customer/place_order.html', form=form, available_chemicals=available_chemicals)

@customer_bp.route('/orders/<int:order_id>')
@login_required
@customer_required
def view_order(order_id):
    """View details of a specific order"""
    order = ChemicalOrder.query.get_or_404(order_id)
    
    # Security check - ensure the order belongs to the current user's organization
    if order.customer_org_id != current_user.organization_id:
        flash('You do not have permission to view this order.', 'error')
        return redirect(url_for('customer_bp.dashboard'))
    
    return render_template('customer/view_order.html', order=order)

@customer_bp.route('/orders/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
@customer_required
def edit_order(order_id):
    """Edit an existing order (only if status is pending)"""
    order = ChemicalOrder.query.get_or_404(order_id)
    
    # Security check - ensure the order belongs to the current user's organization
    if order.customer_org_id != current_user.organization_id:
        flash('You do not have permission to edit this order.', 'error')
        return redirect(url_for('customer_bp.dashboard'))
    
    # Only pending orders can be edited
    if order.status != 'pending':
        flash('Only pending orders can be edited.', 'warning')
        return redirect(url_for('customer_bp.view_order', order_id=order.id))
    
    form = OrderForm()
    available_chemicals = Chemical.query.all()
    if request.method == 'GET':
        # Populate form with existing data
        form.required_by_date.data = order.required_by_date
        form.delivery_address.data = order.delivery_address
        form.special_instructions.data = order.special_instructions
        
        # Prepare items data for the form
        items_data = []
        for item in order.items:
            items_data.append({
                'chemical_name': item.chemical_name,
                'chemical_id': item.chemical_id,
                'quantity': item.quantity,
                'unit': item.unit,
                'unit_price': item.unit_price,
                'special_requirements': item.special_requirements
            })
        
        form.items_data.data = json.dumps(items_data)
    
    if form.validate_on_submit():
        # Update order details
        order.required_by_date = form.required_by_date.data
        order.delivery_address = form.delivery_address.data
        order.special_instructions = form.special_instructions.data
        
        # Remove existing items
        for item in order.items:
            db.session.delete(item)
        
        # Process updated items
        items_data = json.loads(form.items_data.data)
        total_amount = 0.0
        
        for item_data in items_data:
            # Find the chemical by ID if provided
            chemical_id = item_data.get('chemical_id')
            chemical = None
            
            if chemical_id:
                chemical = Chemical.query.get(int(chemical_id))
            
            # Create order item
            item = OrderItem(
                order_id=order.id,
                chemical_name=item_data['chemical_name'],
                chemical_id=chemical.id if chemical else None,
                chemical_cas=item_data.get('chemical_cas', ''),
                quantity=float(item_data['quantity']),
                unit=item_data['unit'],
                unit_price=float(item_data.get('unit_price', 0.0)),
                special_requirements=item_data.get('special_requirements', ''),
                status='pending'
            )
            
            # Add to total amount
            item_total = item.quantity * item.unit_price
            total_amount += item_total
            
            db.session.add(item)
        
        # Update order total
        order.total_amount = total_amount
        
        # Create audit log
        audit_log = AuditLog(
            action_type='order_updated',
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            object_type='ChemicalOrder',
            object_id=order.id,
            description=f"Order {order.order_number} updated with {len(items_data)} items",
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        flash(f'Order {order.order_number} has been successfully updated.', 'success')
        return redirect(url_for('customer_bp.view_order', order_id=order.id))
    
    return render_template('customer/place_order.html', form=form, order=order, is_edit=True, available_chemicals=available_chemicals)

@customer_bp.route('/orders/<int:order_id>/cancel', methods=['GET', 'POST'])
@login_required
@customer_required
def cancel_order(order_id):
    """Cancel an existing order (only if status is pending)"""
    order = ChemicalOrder.query.get_or_404(order_id)
    
    # Security check - ensure the order belongs to the current user's organization
    if order.customer_org_id != current_user.organization_id:
        flash('You do not have permission to cancel this order.', 'error')
        return redirect(url_for('customer_bp.dashboard'))
    
    # Only pending orders can be cancelled
    if order.status != 'pending':
        flash('Only pending orders can be cancelled.', 'warning')
        return redirect(url_for('customer_bp.view_order', order_id=order.id))
    
    if request.method == 'POST':
        # Update order status
        order.status = 'cancelled'
        
        # Create audit log
        audit_log = AuditLog(
            action_type='order_cancelled',
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            object_type='ChemicalOrder',
            object_id=order.id,
            description=f"Order {order.order_number} cancelled by customer",
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        flash(f'Order {order.order_number} has been cancelled.', 'success')
        return redirect(url_for('customer_bp.dashboard'))
    
    return render_template('customer/cancel_order.html', order=order)

@customer_bp.route('/verify-receipt/<int:order_id>', methods=['GET', 'POST'])
@login_required
@customer_required
def verify_receipt(order_id):
    """Route for customers to verify chemical receipts for a specific order"""
    # Get the order first
    order = ChemicalOrder.query.get_or_404(order_id)
    
    # Security check - ensure the order belongs to the current user's organization
    if order.customer_org_id != current_user.organization_id:
        flash('You do not have permission to verify this order.', 'error')
        return redirect(url_for('customer_bp.dashboard'))
    
    # Check if the order status is 'shipped'
    if order.status != 'shipped':
        flash('This order is not ready for receipt verification. Current status: ' + order.status, 'warning')
        return redirect(url_for('customer_bp.view_order', order_id=order.id))
    
    form = VerifyReceiptForm()
    
    if request.method == 'POST':
        try:
            receipt_notes = request.form.get('receipt_notes', '')
            confirm_condition = bool(request.form.get('confirm_condition', False))
            
            # Track if any discrepancies were found
            has_discrepancies = False
            
            # Process each order item
            for item in order.items:
                # Skip items without assigned chemicals
                if not item.assigned_chemical_id:
                    continue
                
                # Get the received quantity for this item
                received_quantity_key = f'received_quantity_{item.id}'
                if received_quantity_key not in request.form:
                    continue
                
                received_quantity = float(request.form.get(received_quantity_key, 0))
                expected_quantity = item.quantity
                
                # Get the chemical
                chemical = Chemical.query.get(item.assigned_chemical_id)
                if not chemical:
                    continue
                
                # Check for quantity discrepancies (allow 2% margin)
                error_margin = 0.02
                acceptable_min = expected_quantity * (1 - error_margin)
                acceptable_max = expected_quantity * (1 + error_margin)
                quantity_discrepancy = received_quantity < acceptable_min or received_quantity > acceptable_max
                
                if quantity_discrepancy:
                    has_discrepancies = True
                    logger.warning(f"Quantity anomaly detected for item {item.id}: Expected {expected_quantity} {item.unit}, received {received_quantity} {item.unit}")
                    
                    # Create blockchain anomaly record
                    anomaly = BlockchainAnomaly(
                        chemical_id=chemical.id,
                        anomaly_type='quantity_discrepancy',
                        description=f"Quantity discrepancy detected. Expected: {expected_quantity} {item.unit}, Received: {received_quantity} {item.unit}",
                        resolution_status='open'
                    )
                    db.session.add(anomaly)
                    
                    flash(f'Warning: The received quantity for {chemical.name} ({received_quantity} {item.unit}) differs significantly from the expected quantity ({expected_quantity} {item.unit}). This anomaly has been recorded.', 'warning')
                
                # Create a movement log for the receipt
                # Find the distributor organization ID - either from the order or use the manufacturer's org
                source_org_id = None
                if hasattr(order, 'distributor_org_id') and order.distributor_org_id:
                    source_org_id = order.distributor_org_id
                elif hasattr(chemical, 'manufacturer_org_id') and chemical.manufacturer_org_id:
                    source_org_id = chemical.manufacturer_org_id
                else:
                    # Fallback to system organization (ID 1) if no source org can be determined
                    source_org_id = 1
                
                movement = MovementLog(
                    tag_id=chemical.rfid_tag,
                    chemical_id=chemical.id,
                    location='Customer Storage',
                    source_location='In Transit',
                    timestamp=datetime.utcnow(),
                    purpose=f'Order receipt #{order.order_number}',
                    status='delivered',
                    remarks=receipt_notes,
                    quantity_moved=received_quantity,
                    moved_by_user_id=current_user.id,
                    source_org_id=source_org_id,
                    destination_org_id=current_user.organization_id
                )
                db.session.add(movement)
                db.session.flush()  # Flush to get the movement ID
                
                # Update the chemical's location and quantity
                chemical.current_location = 'Customer Storage'
                chemical.current_custodian_org_id = current_user.organization_id
                
                # Create receipt record
                receipt = CustomerReceipt(
                    chemical_id=chemical.id,
                    movement_log_id=movement.id,
                    received_quantity=received_quantity,
                    expected_quantity=expected_quantity,
                    quality_check_passed=confirm_condition,
                    quality_remarks=receipt_notes,
                    received_by_user_id=current_user.id,
                    customer_org_id=current_user.organization_id
                )
                db.session.add(receipt)
            
            # Update order status
            order.status = 'delivered'
            order.delivered_at = datetime.utcnow()
            
            # Create audit log
            audit_log = AuditLog(
                action_type='order_received',
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                object_type='ChemicalOrder',
                object_id=order.id,
                description=f"Order {order.order_number} received by customer" + 
                           (" with quantity discrepancies" if has_discrepancies else ""),
                ip_address=request.remote_addr
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            if has_discrepancies:
                flash("Order receipt confirmed with quantity discrepancies. An investigation has been initiated.", 'warning')
            else:
                flash("Order receipt confirmed successfully.", 'success')
            
            return redirect(url_for('customer_bp.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error confirming receipt: {str(e)}", exc_info=True)
            flash(f"Error confirming receipt: {str(e)}", 'error')
    
    return render_template('customer/verify_receipt.html', form=form, order=order)

@customer_bp.route('/confirm-receipt/<int:movement_id>', methods=['GET', 'POST'])
@login_required
@customer_required
def confirm_receipt(movement_id):
    """Route for customers to confirm receipt of chemicals"""
    form = ConfirmReceiptForm()
    
    # Get the movement record
    movement = MovementLog.query.get_or_404(movement_id)
    
    if form.validate_on_submit():
        
        # Check if the movement is intended for this customer's organization
        if movement.destination_org_id != current_user.organization_id:
            flash('This shipment is not intended for your organization.', 'error')
            return render_template('customer/verify_receipt.html', form=form)
        
        # Check if already received
        receipt = CustomerReceipt.query.filter_by(movement_log_id=movement.id).first()
        if receipt:
            flash('This movement has already been verified.', 'warning')
            return render_template('customer/verify_receipt.html', form=form)
        
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
        
        # Get the actual received quantity from the form
        received_quantity = float(form.received_quantity.data) if form.received_quantity.data else movement.quantity_moved
        
        # Check for quantity anomalies
        expected_quantity = movement.quantity_moved
        quantity_discrepancy = False
        anomaly = None
        
        # Allow for a small error margin (2%)
        error_margin = 0.02
        acceptable_min = expected_quantity * (1 - error_margin)
        acceptable_max = expected_quantity * (1 + error_margin)
        
        if received_quantity < acceptable_min or received_quantity > acceptable_max:
            quantity_discrepancy = True
            logger.warning("Quantity anomaly detected: Expected {} {}, received {} {}".format(expected_quantity, chemical.unit, received_quantity, chemical.unit))
            
            # Create blockchain anomaly record
            anomaly = BlockchainAnomaly(
                chemical_id=chemical.id,
                movement_log_id=movement.id,
                anomaly_type='quantity_discrepancy',
                description="Quantity discrepancy detected. Expected: {} {}, Received: {} {}".format(expected_quantity, chemical.unit, received_quantity, chemical.unit),
                resolution_status='open'
            )
            db.session.add(anomaly)
            
            flash(f'Warning: The received quantity ({received_quantity} {chemical.unit}) differs significantly from the expected quantity ({expected_quantity} {chemical.unit}). This anomaly has been recorded.', 'warning')
        
        # Create a receipt record
        receipt = CustomerReceipt(
            movement_log_id=movement.id,
            chemical_id=chemical.id,
            received_quantity=received_quantity,
            expected_quantity=expected_quantity,
            quality_check_passed=form.confirm_condition.data,
            quality_remarks=form.receipt_notes.data,
            received_by_user_id=current_user.id,
            customer_org_id=current_user.organization_id
        )
        
        # Create audit log
        audit_log = AuditLog(
            action_type='receipt_confirmed',
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            object_type='MovementLog',
            object_id=movement.id,
            description="Receipt confirmed for chemical movement {}".format(movement.id) + 
                       (" with quantity anomaly" if quantity_discrepancy else ""),
            ip_address=request.remote_addr
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
                notes=form.receipt_notes.data,
                quantity_anomaly=quantity_discrepancy
            )
            
            if tx_hash:
                movement.receipt_blockchain_tx_hash = tx_hash
                if anomaly:
                    anomaly.blockchain_tx_hash = tx_hash
                flash('Receipt confirmation successfully recorded on blockchain.', 'success')
            else:
                flash('Receipt confirmed but blockchain recording failed. An administrator will review this.', 'warning')
        except Exception as e:
            logger.error(f"Blockchain recording failed: {str(e)}")
            flash(f'Receipt confirmed but blockchain recording failed: {str(e)}. An administrator will review this.', 'warning')
        
        db.session.commit()
        
        if quantity_discrepancy:
            flash("Chemical receipt confirmed with quantity anomaly. An investigation has been initiated.", 'warning')
        else:
            flash("Anomaly report has been submitted.", 'success')
        return redirect(url_for('dashboard_bp.dashboard'))
    
    return render_template('customer/confirm_receipt.html', form=form, movement=movement)

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
