from .extensions import db

class Chemical(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    rfid_tag = db.Column(db.String(120), unique=True, nullable=False)
    manufacturer = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(20), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    storage_condition = db.Column(db.String(100), nullable=True)
    received_date = db.Column(db.Date, nullable=True)
    batch_number = db.Column(db.String(50), nullable=True)
    hazard_class = db.Column(db.String(50), nullable=True)
    cas_number = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    current_location = db.Column(db.String(120), nullable=False, default='Storage')

class MovementLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    moved_by = db.Column(db.String(100), nullable=True)
    purpose = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
