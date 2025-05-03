# from flask import Blueprint, request, jsonify
# from .extensions import db
# from .models import Chemical, MovementLog
# from datetime import datetime

# main = Blueprint('main', __name__)

# @main.route('/register-chemical', methods=['POST'])
# def register_chemical():
#     data = request.get_json()
#     new_chemical = Chemical(
#         name=data['name'],
#         rfid_tag=data['rfid_tag']
#     )
#     db.session.add(new_chemical)
#     db.session.commit()
#     return jsonify({'message': 'Chemical registered successfully'}), 201

# @main.route('/log-event', methods=['POST'])
# def log_event():
#     data = request.get_json()
#     new_log = MovementLog(
#         tag_id=data['tag_id'],
#         location=data['location'],
#         timestamp=datetime.utcnow()
#     )
#     db.session.add(new_log)
#     db.session.commit()
#     return jsonify({'message': 'Event logged successfully'}), 201

# @main.route('/chemical-history/<tag_id>', methods=['GET'])
# def chemical_history(tag_id):
#     logs = MovementLog.query.filter_by(tag_id=tag_id).all()
#     history = [{
#         'location': log.location,
#         'timestamp': log.timestamp.isoformat()
#     } for log in logs]
#     return jsonify({'history': history}), 200
