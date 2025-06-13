from .extensions import db
from flask_login import UserMixin
from datetime import datetime
import enum
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

# Define role types as enum for better type checking
class RoleType(enum.Enum):
    ADMIN = "admin"
    MANUFACTURER = "manufacturer"
    DISTRIBUTOR = "distributor"
    CUSTOMER = "customer"

# Organization model
class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email_domain = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    # Define the permissions this organization has
    can_manufacture = db.Column(db.Boolean, default=False)
    can_distribute = db.Column(db.Boolean, default=False)
    can_receive = db.Column(db.Boolean, default=False)
    
    # Relationships
    users = db.relationship('User', backref='organization', lazy=True)
    
    def __repr__(self):
        return f"<Organization {self.name}>"

# User model with UserMixin for flask-login
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    role = db.Column(db.Enum(RoleType), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Foreign keys
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    
    # Special flag for admin user
    is_admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<User {self.username}>"
        
    def set_password(self, password):
        """Set the password hash for the user."""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
        
    def get_id(self):
        """Return the user ID as a unicode string for Flask-Login."""
        return str(self.id)
    
    def has_role(self, role_type):
        if self.is_admin:
            return True
        if role_type == RoleType.ADMIN:
            return self.is_admin
        if role_type == RoleType.MANUFACTURER:
            return self.organization and self.organization.can_manufacture and self.role == RoleType.MANUFACTURER
        if role_type == RoleType.DISTRIBUTOR:
            return self.organization and self.organization.can_distribute and self.role == RoleType.DISTRIBUTOR
        if role_type == RoleType.CUSTOMER:
            return self.organization and self.organization.can_receive and self.role == RoleType.CUSTOMER
        return False

# RFID Device model for hardware integration
class RFIDDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    active = db.Column(db.Boolean, default=True)
    last_seen = db.Column(db.DateTime, nullable=True)
    
    # Foreign key to organization that owns this device
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    registered_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f"<RFIDDevice {self.device_id}>"

class Chemical(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    rfid_tag = db.Column(db.String(120), unique=True, nullable=False)
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
    
    # Additional fields for RBAC
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys for relationships
    registered_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manufacturer_org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    current_custodian_org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    # Relationships
    registered_by = db.relationship('User', foreign_keys=[registered_by_user_id], backref='registered_chemicals')
    manufacturer_org = db.relationship('Organization', foreign_keys=[manufacturer_org_id], backref='manufactured_chemicals')
    current_custodian = db.relationship('Organization', foreign_keys=[current_custodian_org_id], backref='possessed_chemicals')
    
    def __repr__(self):
        return f"<Chemical {self.name} ({self.rfid_tag})>"

class MovementLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    purpose = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    validation_status = db.Column(db.String(20), nullable=False, default='pending')  # Values: 'verified', 'suspicious', 'pending'
    blockchain_recorded = db.Column(db.Boolean, default=False)  # Track if this was recorded on the blockchain
    
    # Additional fields for RBAC
    source_location = db.Column(db.String(120), nullable=True)  # Where the chemical was moved from
    quantity_moved = db.Column(db.Float, nullable=True)  # How much was moved (if partial)
    
    # Hardware integration fields
    rfid_device_id = db.Column(db.Integer, db.ForeignKey('rfid_device.id'), nullable=True)  # If logged via hardware
    
    # Foreign keys for relationships
    moved_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source_org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    destination_org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    chemical_id = db.Column(db.Integer, db.ForeignKey('chemical.id'), nullable=False)
    
    # Relationships
    moved_by_user = db.relationship('User', backref='movement_logs')
    source_org = db.relationship('Organization', foreign_keys=[source_org_id], backref='outgoing_movements')
    destination_org = db.relationship('Organization', foreign_keys=[destination_org_id], backref='incoming_movements')
    chemical = db.relationship('Chemical', backref='movement_logs')
    rfid_device = db.relationship('RFIDDevice', backref='movement_logs')
    
    def __repr__(self):
        return f"<MovementLog {self.id} for {self.tag_id} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}>"
    
    # Method to check if this movement is authorized based on RBAC
    def is_authorized(self):
        # Check if user has permission to distribute chemicals
        if not self.moved_by_user.has_role(RoleType.DISTRIBUTOR) and not self.moved_by_user.is_admin:
            return False
            
        # Check if the user's organization has distribution rights
        if not self.moved_by_user.organization.can_distribute and not self.moved_by_user.is_admin:
            return False
            
        return True


# Customer Receipt model for final delivery confirmation
class CustomerReceipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movement_log_id = db.Column(db.Integer, db.ForeignKey('movement_log.id'), nullable=False)
    chemical_id = db.Column(db.Integer, db.ForeignKey('chemical.id'), nullable=False)
    received_quantity = db.Column(db.Float, nullable=True)
    expected_quantity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    quality_check_passed = db.Column(db.Boolean, nullable=True)
    quality_remarks = db.Column(db.Text, nullable=True)
    received_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    # Relationships
    movement_log = db.relationship('MovementLog', backref='receipt')
    chemical = db.relationship('Chemical', backref='receipts')
    received_by = db.relationship('User', backref='receipts_confirmed')
    customer_org = db.relationship('Organization', backref='receipts')
    
    def __repr__(self):
        return f"<Receipt {self.id} for {self.chemical.name}>"


# Audit log for tracking all important actions
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(50), nullable=False)  # e.g., 'chemical_registration', 'movement_log', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    object_type = db.Column(db.String(50), nullable=False)  # Model name affected
    object_id = db.Column(db.Integer, nullable=True)       # Primary key of affected record
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    success = db.Column(db.Boolean, default=True)          # Was the action successful?
    additional_data = db.Column(db.Text, nullable=True)     # JSON string for additional context
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    organization = db.relationship('Organization', backref='audit_logs')
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action_type} by {self.user.username}>"


# Blockchain Anomaly Detection record
class BlockchainAnomaly(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chemical_id = db.Column(db.Integer, db.ForeignKey('chemical.id'), nullable=False)
    movement_log_id = db.Column(db.Integer, db.ForeignKey('movement_log.id'), nullable=True)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    anomaly_type = db.Column(db.String(50), nullable=False)  # e.g., 'unauthorized_registration', 'location_mismatch'
    description = db.Column(db.Text, nullable=False)
    blockchain_tx_hash = db.Column(db.String(100), nullable=True)  # Hash of transaction with anomaly
    resolution_status = db.Column(db.String(20), default='open')  # Values: 'open', 'investigating', 'resolved', 'false_positive'
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    chemical = db.relationship('Chemical', backref='anomalies')
    movement_log = db.relationship('MovementLog', backref='anomalies')
    resolved_by = db.relationship('User', backref='resolved_anomalies')
    
    def __repr__(self):
        return f"<BlockchainAnomaly {self.id}: {self.anomaly_type} for {self.chemical.rfid_tag}>"


# Function to create admin user and system organization
def create_admin_user(db_session):
    """Create the admin user if it doesn't exist"""
    # Check if admin exists
    admin_user = User.query.filter_by(email='admin@gmail.com').first()
    if not admin_user:
        # Create system organization first
        system_org = Organization.query.filter_by(name='System').first()
        if not system_org:
            system_org = Organization(
                name='System',
                email_domain='gmail.com',
                description='System organization for administration',
                can_manufacture=True,
                can_distribute=True,
                can_receive=True
            )
            db_session.add(system_org)
            db_session.commit()
            logger.info("Created system organization")
            
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@gmail.com',
            first_name='System',
            last_name='Admin',
            role=RoleType.ADMIN,
            is_admin=True,
            organization_id=system_org.id
        )
        admin_user.set_password('Admin@123')  # Default password, should be changed immediately
        db_session.add(admin_user)
        db_session.commit()
        logger.info("Created admin user with default credentials")
        
        # Create audit log for admin user creation
        audit = AuditLog(
            action_type='system_initialization',
            user_id=admin_user.id,
            organization_id=system_org.id,
            object_type='User',
            object_id=admin_user.id,
            description='System initialized with admin user creation',
        )
        db_session.add(audit)
        db_session.commit()
        
        return admin_user, True  # Return user and created flag
    
    return admin_user, False  # User already existed
