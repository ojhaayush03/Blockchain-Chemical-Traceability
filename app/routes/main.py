from flask import Blueprint, request, jsonify, redirect, url_for
from app.extensions import db
from app.models import Chemical, MovementLog
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/register-chemical', methods=['POST'])
def register_chemical():
    data = request.get_json()
    new_chemical = Chemical(
        name=data['name'],
        rfid_tag=data['rfid_tag']
    )
    db.session.add(new_chemical)
    db.session.commit()
    return jsonify({'message': 'Chemical registered successfully'}), 201

@main.route('/log-event', methods=['POST'])
def log_event():
    try:
        # Try to get JSON data first
        if request.is_json:
            data = request.get_json()
        else:
            # Fall back to form data if not JSON
            data = request.form.to_dict()
        
        # Validate required fields
        if 'tag_id' not in data or 'location' not in data:
            return jsonify({'error': 'Missing required fields: tag_id and location are required'}), 400
        
        # Create new movement log with all fields
        new_log = MovementLog(
            tag_id=data['tag_id'],
            location=data['location'],
            timestamp=datetime.utcnow(),
            moved_by=data.get('moved_by'),
            purpose=data.get('purpose'),
            status=data.get('status'),
            remarks=data.get('remarks')
        )
        
        # Update the chemical's current location
        chemical = Chemical.query.filter_by(rfid_tag=data['tag_id']).first()
        if chemical:
            chemical.current_location = data['location']
        else:
            # Log a warning but don't fail if chemical not found
            print(f"Warning: No chemical found with RFID tag {data['tag_id']}")
        
        db.session.add(new_log)
        db.session.commit()
        
        # Return JSON response for API calls, or redirect for form submissions
        if request.is_json:
            return jsonify({'message': 'Event logged successfully'}), 201
        else:
            return redirect(url_for('dashboard_bp.dashboard'))
            
    except Exception as e:
        # Roll back any changes and return error
        db.session.rollback()
        error_msg = str(e)
        print(f"Error in log_event: {error_msg}")
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        else:
            return f"Error logging event: {error_msg}", 500

@main.route('/chemical-history/<tag_id>', methods=['GET'])
def chemical_history(tag_id):
    logs = MovementLog.query.filter_by(tag_id=tag_id).order_by(MovementLog.timestamp.desc()).all()
    history = [{
        'location': log.location,
        'timestamp': log.timestamp.isoformat(),
        'status': log.status,
        'moved_by': log.moved_by,
        'purpose': log.purpose,
        'remarks': log.remarks
    } for log in logs]
    return jsonify({'history': history}), 200
