from .extensions import db

class Chemical(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    rfid_tag = db.Column(db.String(120), unique=True, nullable=False)

class MovementLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
