from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models import Chemical, MovementLog, AuditLog, Organization, ChemicalOrder, OrderItem
from app.forms import MovementForm
from app import db
from app.decorators import distributor_required

# Import blockchain client if available
try:
    from app.blockchain_client import BlockchainClient
except ImportError:
    BlockchainClient = None

distributor_bp = Blueprint('distributor_bp', __name__, url_prefix='/distributor')

@distributor_bp.route('/dashboard')
@login_required
@distributor_required
def dashboard():
    """Distributor dashboard showing orders and movements"""
    # Get all orders assigned to this distributor's organization
    orders = ChemicalOrder.query.filter(
        ChemicalOrder.status.in_(['pending', 'approved', 'processing', 'shipped'])
    ).order_by(ChemicalOrder.order_date.desc()).all()
    
    # Get recent movements (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    movements = MovementLog.query.filter(
        MovementLog.timestamp >= thirty_days_ago
    ).order_by(MovementLog.timestamp.desc()).all()
    
    # Calculate dashboard statistics
    pending_orders = sum(1 for order in orders if order.status == 'pending')
    processing_orders = sum(1 for order in orders if order.status == 'processing')
    shipped_orders = sum(1 for order in orders if order.status == 'shipped')
    completed_orders = sum(1 for order in orders if order.status == 'delivered')
    
    stats = {
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'completed_orders': completed_orders
    }
    
    return render_template(
        'distributor/dashboard.html',
        orders=orders,
        movements=movements,
        stats=stats
    )

@distributor_bp.route('/manage-orders')
@login_required
@distributor_required
def manage_orders():
    """View and manage all customer orders"""
    orders = ChemicalOrder.query.order_by(ChemicalOrder.order_date.desc()).all()
    
    # Calculate dashboard statistics
    pending_orders = sum(1 for order in orders if order.status == 'pending')
    processing_orders = sum(1 for order in orders if order.status == 'processing')
    shipped_orders = sum(1 for order in orders if order.status == 'shipped')
    completed_orders = sum(1 for order in orders if order.status == 'delivered')
    
    stats = {
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'completed_orders': completed_orders
    }
    
    # Get all customer organizations for filtering
    # Find organizations that can receive chemicals (customers)
    organizations = Organization.query.filter_by(can_receive=True).all()
    
    return render_template('distributor/manage_orders.html', 
                           orders=orders, 
                           stats=stats, 
                           organizations=organizations)

@distributor_bp.route('/approve-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
@distributor_required
def approve_order(order_id):
    """Approve a pending customer order"""
    order = ChemicalOrder.query.get_or_404(order_id)
    
    # Only pending orders can be approved
    if order.status != 'pending':
        flash('Only pending orders can be approved.', 'warning')
        return redirect(url_for('distributor_bp.view_order', order_id=order.id))
    
    if request.method == 'POST':
        # Update order status
        order.status = 'approved'
        order.approved_by = current_user.id
        order.approved_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            action_type='order_approved',
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            object_type='ChemicalOrder',
            object_id=order.id,
            description=f"Order {order.order_number} approved by {current_user.username}",
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        flash(f'Order {order.order_number} has been approved.', 'success')
        return redirect(url_for('distributor_bp.dashboard'))
    
    return render_template('distributor/approve_order.html', order=order)

@distributor_bp.route('/process-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
@distributor_required
def process_order(order_id):
    """Process an approved order by assigning chemicals"""
    order = ChemicalOrder.query.get_or_404(order_id)
    
    # Only approved orders can be processed
    if order.status != 'approved':
        flash('Only approved orders can be processed.', 'warning')
        return redirect(url_for('distributor_bp.view_order', order_id=order.id))
    
    # Get available chemicals for each order item
    order_items = {}
    for item in order.items:
        # Find matching chemicals by name and CAS number
        matching_chemicals = Chemical.query.filter(
            Chemical.name == item.chemical_name,
            Chemical.current_location == 'Storage'
        ).all()
        
        order_items[item.id] = {
            'item': item,
            'available_chemicals': matching_chemicals
        }
    
    if request.method == 'POST':
        # Process form data
        all_assigned = True
        for item in order.items:
            chemical_id = request.form.get(f'chemical_{item.id}')
            if not chemical_id:
                all_assigned = False
                continue
                
            # Assign chemical to order item
            item.assigned_chemical_id = chemical_id
        
        if all_assigned:
            # Update order status
            order.status = 'processing'
            order.processed_by = current_user.id
            order.processed_at = datetime.utcnow()
            
            # Create audit log
            audit_log = AuditLog(
                action_type='order_processed',
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                object_type='ChemicalOrder',
                object_id=order.id,
                description=f"Order {order.order_number} processed and chemicals assigned",
                ip_address=request.remote_addr
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash(f'Order {order.order_number} has been processed and is ready for shipping.', 'success')
            return redirect(url_for('distributor_bp.dashboard'))
        else:
            flash('All order items must be assigned a chemical.', 'warning')
    
    return render_template('distributor/process_order.html', order=order, order_items=order_items)

@distributor_bp.route('/ship-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
@distributor_required
def ship_order(order_id):
    """Ship a processed order to the customer"""
    order = ChemicalOrder.query.get_or_404(order_id)
    
    # Only processing orders can be shipped
    if order.status != 'processing':
        flash('Only processed orders can be shipped.', 'warning')
        return redirect(url_for('distributor_bp.view_order', order_id=order.id))
    
    if request.method == 'POST':
        tracking_number = request.form.get('tracking_number')
        carrier = request.form.get('carrier')
        estimated_delivery = request.form.get('estimated_delivery')
        
        # Update order status
        order.status = 'shipped'
        order.shipped_by = current_user.id
        order.shipped_at = datetime.utcnow()
        order.tracking_number = tracking_number
        order.carrier = carrier
        if estimated_delivery:
            # Handle datetime-local format which includes time component
            try:
                # Try to parse with datetime format first
                order.estimated_delivery = datetime.strptime(estimated_delivery, '%Y-%m-%dT%H:%M')
            except ValueError:
                # Fall back to date-only format
                order.estimated_delivery = datetime.strptime(estimated_delivery.split('T')[0], '%Y-%m-%d')
        
        # Create movement logs for each chemical
        for item in order.items:
            if not item.assigned_chemical_id:
                continue
                
            chemical = Chemical.query.get(item.assigned_chemical_id)
            if not chemical:
                continue
                
            # Update chemical location
            chemical.current_location = 'In Transit'
            chemical.current_custodian_org_id = current_user.organization_id
            
            # Create movement log
            movement = MovementLog(
                tag_id=chemical.rfid_tag,
                location='In Transit',
                timestamp=datetime.utcnow(),
                purpose=f'Order shipment #{order.order_number} (Tracking: {tracking_number}, Carrier: {carrier})',
                status='in_transit',
                source_location='Storage',
                source_org_id=current_user.organization_id,
                destination_org_id=order.customer_org_id,
                moved_by_user_id=current_user.id,
                chemical_id=chemical.id
            )
            db.session.add(movement)
        
        # Create audit log
        audit_log = AuditLog(
            action_type='order_shipped',
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            object_type='ChemicalOrder',
            object_id=order.id,
            description=f"Order {order.order_number} shipped to customer via {carrier}, tracking: {tracking_number}",
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        flash(f'Order {order.order_number} has been shipped to the customer.', 'success')
        return redirect(url_for('distributor_bp.dashboard'))
    
    return render_template('distributor/ship_order.html', order=order)

@distributor_bp.route('/view-order/<int:order_id>')
@login_required
@distributor_required
def view_order(order_id):
    """View details of a specific order"""
    order = ChemicalOrder.query.get_or_404(order_id)
    return render_template('distributor/view_order.html', order=order)

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

# This route is already defined above, removing duplicate

# This route is already defined above, removing duplicate

# This route is already defined above, removing duplicate
@distributor_bp.route('/orders/<int:order_id>/approve', methods=['GET', 'POST'])
@login_required
@distributor_required
def approve_order_duplicate(order_id):
    """Route for distributors to approve a pending order"""
    order = ChemicalOrder.query.get_or_404(order_id)
    
    # Check if order is in pending status
    if order.status != 'pending':
        flash('This order cannot be approved because it is not in pending status.', 'warning')
        return redirect(url_for('distributor_bp.view_order', order_id=order.id))
    
    if request.method == 'POST':
        # Update order status to approved
        order.status = 'approved'
        order.approved_by_user_id = current_user.id
        order.approved_date = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            action='order_approved',
            object_type='order',
            object_id=order.id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            details=f"Order #{order.order_number} approved by {current_user.email}"
        )
        db.session.add(audit_log)
        
        try:
            db.session.commit()
            flash(f'Order #{order.order_number} has been approved successfully.', 'success')
            
            # TODO: Send notification to customer about order approval
            
            return redirect(url_for('distributor_bp.manage_orders'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error approving order: {str(e)}', 'error')
            return redirect(url_for('distributor_bp.view_order', order_id=order.id))
    
    return render_template('distributor/approve_order.html', order=order)

# This route is already defined above, removing duplicate
@distributor_bp.route('/orders/<int:order_id>/process', methods=['GET', 'POST'])
@login_required
@distributor_required
def process_order_duplicate(order_id):
    """Route for distributors to process an approved order"""
    order = ChemicalOrder.query.get_or_404(order_id)
    
    # Check if order is in approved status
    if order.status != 'approved':
        flash('This order cannot be processed because it is not in approved status.', 'warning')
        return redirect(url_for('distributor_bp.view_order', order_id=order.id))
    
    if request.method == 'POST':
        # Get chemical assignments from form
        chemical_assignments = {}
        for item in order.items:
            chemical_id = request.form.get(f'chemical_{item.id}')
            if chemical_id:
                chemical_assignments[item.id] = int(chemical_id)
        
        # Validate that all items have assigned chemicals
        if len(chemical_assignments) != len(order.items):
            flash('All order items must have assigned chemicals.', 'error')
            return redirect(url_for('distributor_bp.process_order', order_id=order.id))
        
        # Update order status to processing
        order.status = 'processing'
        order.processing_date = datetime.utcnow()
        order.processed_by_user_id = current_user.id
        
        # Store chemical assignments in order metadata
        if not order.metadata:
            order.metadata = {}
        order.metadata['chemical_assignments'] = chemical_assignments
        
        # Create audit log
        audit_log = AuditLog(
            action='order_processing',
            object_type='order',
            object_id=order.id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            details=f"Order #{order.order_number} processing started by {current_user.email}"
        )
        db.session.add(audit_log)
        
        try:
            db.session.commit()
            flash(f'Order #{order.order_number} is now being processed.', 'success')
            
            # TODO: Send notification to customer about order processing
            
            return redirect(url_for('distributor_bp.manage_orders'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing order: {str(e)}', 'error')
    
    # Get available chemicals for each order item
    available_chemicals = {}
    for item in order.items:
        # Find chemicals that match the name or CAS number and have sufficient quantity
        matching_chemicals = Chemical.query.filter(
            (Chemical.name == item.chemical_name) | 
            (Chemical.cas_number == item.chemical_cas if item.chemical_cas else False)
        ).filter(
            Chemical.quantity >= item.quantity,
            Chemical.current_custodian_org_id == current_user.organization_id
        ).all()
        
        available_chemicals[item.id] = matching_chemicals
    
    return render_template('distributor/process_order.html', 
                           order=order,
                           available_chemicals=available_chemicals)

# This route is already defined above, removing duplicate
@distributor_bp.route('/orders/<int:order_id>/ship', methods=['GET', 'POST'])
@login_required
@distributor_required
def ship_order_duplicate(order_id):
    """Route for distributors to ship a processed order"""
    order = ChemicalOrder.query.get_or_404(order_id)
    
    # Check if order is in processing status
    if order.status != 'processing':
        flash('This order cannot be shipped because it is not in processing status.', 'warning')
        return redirect(url_for('distributor_bp.view_order', order_id=order.id))
    
    if request.method == 'POST':
        # Get shipping details from form
        tracking_number = request.form.get('tracking_number')
        carrier = request.form.get('carrier')
        estimated_delivery = datetime.strptime(request.form.get('estimated_delivery'), '%Y-%m-%dT%H:%M')
        shipping_notes = request.form.get('shipping_notes')
        
        # Update order status to shipped
        order.status = 'shipped'
        order.shipped_date = datetime.utcnow()
        order.shipped_by_user_id = current_user.id
        
        # Store shipping details in order metadata
        if not order.metadata:
            order.metadata = {}
        order.metadata['shipping'] = {
            'tracking_number': tracking_number,
            'carrier': carrier,
            'estimated_delivery': estimated_delivery.isoformat(),
            'shipping_notes': shipping_notes
        }
        
        # Create movement logs for each chemical in the order
        chemical_assignments = order.metadata.get('chemical_assignments', {})
        movement_logs = []
        
        for item_id, chemical_id in chemical_assignments.items():
            item = OrderItem.query.get(int(item_id))
            chemical = Chemical.query.get(int(chemical_id))
            
            if item and chemical:
                # Create movement log
                movement = MovementLog(
                    tag_id=chemical.rfid_tag,
                    chemical_id=chemical.id,
                    location='In Transit',
                    source_location=chemical.current_location,
                    destination_location=order.delivery_address,
                    timestamp=datetime.utcnow(),
                    purpose='shipping',
                    status='in_transit',
                    remarks=f"Shipped as part of order #{order.order_number}",
                    quantity_moved=item.quantity,
                    moved_by_user_id=current_user.id,
                    source_org_id=current_user.organization_id,
                    destination_org_id=order.customer_org_id,
                    tracking_number=tracking_number
                )
                
                db.session.add(movement)
                movement_logs.append(movement)
                
                # Update chemical quantity and location
                chemical.quantity -= item.quantity
                chemical.current_location = 'In Transit'
                chemical.last_updated = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            action='order_shipped',
            object_type='order',
            object_id=order.id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            details=f"Order #{order.order_number} shipped by {current_user.email} with tracking #{tracking_number}"
        )
        db.session.add(audit_log)
        
        try:
            db.session.commit()
            flash(f'Order #{order.order_number} has been shipped successfully.', 'success')
            
            # Try to record on blockchain if available
            if BlockchainClient:
                try:
                    blockchain_client = BlockchainClient()
                    for movement in movement_logs:
                        tx_hash = blockchain_client.record_movement(
                            movement_id=str(movement.id),
                            chemical_id=movement.chemical_id,
                            source=movement.source_location,
                            destination=movement.destination_location,
                            timestamp=movement.timestamp.isoformat(),
                            distributor_id=current_user.organization_id
                        )
                        
                        if tx_hash:
                            movement.blockchain_recorded = True
                except Exception as e:
                    flash(f'Order shipped but blockchain recording failed: {str(e)}. An administrator will review this.', 'warning')
            
            # TODO: Send notification to customer about order shipment
            
            return redirect(url_for('distributor_bp.manage_orders'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error shipping order: {str(e)}', 'error')
    
    return render_template('distributor/ship_order.html', order=order)
