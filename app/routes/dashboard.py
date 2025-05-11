from flask import Blueprint, render_template, request, redirect, url_for
from app.extensions import db
from app.models import Chemical, MovementLog  # Import MovementLog as well
from datetime import datetime

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    chemicals = Chemical.query.all()
    return render_template('dashboard.html', chemicals=chemicals)

@dashboard_bp.route('/chemical/<int:chemical_id>')
def chemical_detail(chemical_id):
    chemical = Chemical.query.get_or_404(chemical_id)
    # Get movement logs for this chemical's RFID tag
    movement_logs = MovementLog.query.filter_by(tag_id=chemical.rfid_tag).order_by(MovementLog.timestamp.desc()).all()
    return render_template('chemical_detail.html', chemical=chemical, logs=movement_logs)

@dashboard_bp.route('/add_chemical', methods=['POST'])
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
        
        # Create new chemical
        new_chemical = Chemical(
            name=name,
            rfid_tag=rfid_tag,
            manufacturer=manufacturer,
            quantity=float(quantity) if quantity else None,
            unit=unit,
            expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None,
            storage_condition=storage_condition,
            received_date=datetime.strptime(received_date, '%Y-%m-%d').date() if received_date else None,
            batch_number=batch_number,
            hazard_class=hazard_class,
            cas_number=cas_number,
            description=description,
            current_location=request.form.get('current_location', 'Storage')
        )
        
        # Add to database
        db.session.add(new_chemical)
        db.session.commit()
        
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
