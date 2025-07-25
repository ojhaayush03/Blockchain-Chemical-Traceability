from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, FileField, HiddenField
from wtforms.fields import DateField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, Regexp
from app.models import User, Organization

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    organization_name = StringField('Organization Name', validators=[DataRequired()])
    organization_domain = StringField('Organization Email Domain', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_organization_domain(self, organization_domain):
        org = Organization.query.filter_by(email_domain=organization_domain.data).first()
        if org is not None:
            raise ValidationError('This organization domain is already registered.')

class OrganizationForm(FlaskForm):
    name = StringField('Organization Name', validators=[DataRequired(), Length(min=2, max=100)])
    email_domain = StringField('Email Domain', validators=[
        DataRequired(), 
        Regexp(r'^[a-zA-Z0-9]+([\-\.]{1}[a-zA-Z0-9]+)*\.[a-zA-Z]{2,}$', 
               message="Please enter a valid domain (e.g., company.com)")
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    can_manufacture = BooleanField('Manufacturer Permission')
    can_distribute = BooleanField('Distributor Permission')
    can_receive = BooleanField('Customer Permission')
    active = BooleanField('Active')
    submit = SubmitField('Save Organization')

    def validate_email_domain(self, email_domain):
        org = Organization.query.filter_by(email_domain=email_domain.data).first()
        if org is not None and org.id != self.id.data:
            raise ValidationError('This email domain is already registered.')

class ChemicalForm(FlaskForm):
    name = StringField('Chemical Name', validators=[DataRequired(), Length(max=100)])
    chemical_formula = StringField('Chemical Formula', validators=[DataRequired(), Length(max=50)])
    cas_number = StringField('CAS Number', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    physical_state = SelectField('Physical State', choices=[
        ('solid', 'Solid'),
        ('liquid', 'Liquid'),
        ('gas', 'Gas')
    ], validators=[DataRequired()])
    hazard_class = SelectField('Hazard Class', choices=[
        ('non_hazardous', 'Non-Hazardous'),
        ('flammable', 'Flammable'),
        ('corrosive', 'Corrosive'),
        ('toxic', 'Toxic'),
        ('oxidizing', 'Oxidizing'),
        ('explosive', 'Explosive')
    ], validators=[DataRequired()])
    batch_number = StringField('Batch Number', validators=[DataRequired(), Length(max=50)])
    manufacturing_date = DateTimeField('Manufacturing Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    expiry_date = DateTimeField('Expiry Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    unit = SelectField('Unit', choices=[
        ('kg', 'Kilograms'),
        ('g', 'Grams'),
        ('l', 'Liters'),
        ('ml', 'Milliliters')
    ], validators=[DataRequired()])
    storage_conditions = TextAreaField('Storage Conditions', validators=[Optional(), Length(max=200)])
    rfid_tag = StringField('RFID Tag', validators=[DataRequired(), Length(max=100)])
    current_location = StringField('Current Location', validators=[DataRequired(), Length(max=100)])
    blockchain_register = BooleanField('Register on Blockchain')
    submit = SubmitField('Register Chemical')

class ChemicalRegistrationForm(FlaskForm):
    name = StringField('Chemical Name', validators=[DataRequired(), Length(max=100)])
    cas_number = StringField('CAS Number', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    chemical_formula = StringField('Chemical Formula', validators=[Optional(), Length(max=50)])
    hazard_class = SelectField('Hazard Class', choices=[
        ('non_hazardous', 'Non-Hazardous'),
        ('flammable', 'Flammable'),
        ('corrosive', 'Corrosive'),
        ('toxic', 'Toxic'),
        ('oxidizing', 'Oxidizing'),
        ('explosive', 'Explosive')
    ], validators=[DataRequired()])
    batch_number = StringField('Batch Number', validators=[DataRequired(), Length(max=50)])
    manufacturing_date = DateField('Manufacturing Date', format='%Y-%m-%d', validators=[Optional()])
    expiry_date = DateField('Expiry Date', format='%Y-%m-%d', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    unit = SelectField('Unit', choices=[
        ('kg', 'Kilograms'),
        ('g', 'Grams'),
        ('l', 'Liters'),
        ('ml', 'Milliliters')
    ], validators=[DataRequired()])
    storage_condition = TextAreaField('Storage Conditions', validators=[Optional(), Length(max=200)])
    handling_instructions = TextAreaField('Handling Instructions', validators=[Optional(), Length(max=500)])
    rfid_tag = StringField('RFID Tag', validators=[Optional(), Length(max=100)])
    initial_location = StringField('Initial Location', validators=[Optional(), Length(max=100)])
    msds_document = FileField('MSDS Document', validators=[Optional()])
    blockchain_register = BooleanField('Register on Blockchain')
    confirm_accuracy = BooleanField('I confirm that all information provided is accurate', validators=[DataRequired()])
    submit = SubmitField('Register Chemical')

class MovementForm(FlaskForm):
    rfid_tag = StringField('RFID Tag', validators=[DataRequired(), Length(max=100)])
    chemical_id = HiddenField('Chemical ID', validators=[DataRequired()])
    movement_type = SelectField('Movement Type', choices=[
        ('transfer', 'Transfer to Another Location'),
        ('shipping', 'Shipping to Customer'),
        ('return', 'Return to Manufacturer')
    ], validators=[DataRequired()])
    source_location = StringField('Source Location', validators=[DataRequired(), Length(max=100)])
    destination_location = StringField('Destination Location', validators=[DataRequired(), Length(max=100)])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    unit = StringField('Unit', validators=[DataRequired(), Length(max=20)])
    recipient_organization = SelectField('Recipient Organization', coerce=int, validators=[DataRequired()])
    recipient_email = StringField('Recipient Email', validators=[DataRequired(), Email()])
    transport_method = SelectField('Transport Method', choices=[
        ('road', 'Road Transport'),
        ('rail', 'Rail Transport'),
        ('air', 'Air Transport'),
        ('sea', 'Sea Transport')
    ], validators=[DataRequired()])
    estimated_arrival = DateTimeField('Estimated Arrival', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    temperature_controlled = BooleanField('Temperature Controlled')
    min_temperature = FloatField('Minimum Temperature (°C)', validators=[Optional()])
    max_temperature = FloatField('Maximum Temperature (°C)', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    confirm_accuracy = BooleanField('I confirm that all information is accurate', validators=[DataRequired()])
    submit = SubmitField('Log Movement')

class ShipmentForm(FlaskForm):
    tracking_number = StringField('Tracking Number', validators=[DataRequired(), Length(max=100)])
    carrier = SelectField('Carrier', choices=[
        ('fedex', 'FedEx'),
        ('ups', 'UPS'),
        ('dhl', 'DHL'),
        ('usps', 'USPS'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    estimated_delivery = DateTimeField('Estimated Delivery Date', format='%Y-%m-%d', validators=[DataRequired()])
    special_handling = BooleanField('Requires Special Handling')
    handling_instructions = TextAreaField('Handling Instructions', validators=[Optional(), Length(max=500)])
    temperature_controlled = BooleanField('Temperature Controlled')
    min_temperature = FloatField('Minimum Temperature (°C)', validators=[Optional()])
    max_temperature = FloatField('Maximum Temperature (°C)', validators=[Optional()])
    notes = TextAreaField('Shipping Notes', validators=[Optional(), Length(max=500)])
    confirm_accuracy = BooleanField('I confirm that all information is accurate', validators=[DataRequired()])
    submit = SubmitField('Ship Order')

class VerifyReceiptForm(FlaskForm):
    movement_id = StringField('Movement ID', validators=[DataRequired(), Length(max=100)])
    rfid_tag = StringField('RFID Tag', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Verify Shipment')

class ConfirmReceiptForm(FlaskForm):
    movement_id = HiddenField('Movement ID', validators=[DataRequired()])
    receipt_notes = TextAreaField('Receipt Notes', validators=[Optional(), Length(max=500)])
    received_quantity = FloatField('Actual Received Quantity', validators=[Optional()])
    confirm_quantity = BooleanField('Confirm Quantity Matches', validators=[DataRequired()])
    confirm_condition = BooleanField('Confirm Good Condition', validators=[DataRequired()])
    rfid_tag = StringField('RFID Tag Verification', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Confirm Receipt')

class AnomalyResolutionForm(FlaskForm):
    anomaly_id = HiddenField('Anomaly ID', validators=[DataRequired()])
    resolution_notes = TextAreaField('Resolution Notes', validators=[DataRequired(), Length(max=500)])
    resolution_status = SelectField('Resolution Status', choices=[
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
        ('escalated', 'Escalated to Authority')
    ], validators=[DataRequired()])
    submit = SubmitField('Submit Resolution')

class OrderItemForm(FlaskForm):
    chemical_name = StringField('Chemical Name', validators=[DataRequired(), Length(max=100)])
    chemical_cas = StringField('CAS Number', validators=[Optional(), Length(max=20)])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    unit = SelectField('Unit', choices=[
        ('kg', 'Kilograms'),
        ('g', 'Grams'),
        ('l', 'Liters'),
        ('ml', 'Milliliters')
    ], validators=[DataRequired()])
    unit_price = FloatField('Unit Price', validators=[Optional()])
    special_requirements = TextAreaField('Special Requirements', validators=[Optional(), Length(max=200)])

class OrderForm(FlaskForm):
    required_by_date = DateField('Required By Date', format='%Y-%m-%d', validators=[Optional()])
    delivery_address = TextAreaField('Delivery Address', validators=[DataRequired(), Length(max=500)])
    special_instructions = TextAreaField('Special Instructions', validators=[Optional(), Length(max=500)])
    items_data = HiddenField('Items Data', validators=[DataRequired()])
    confirm_terms = BooleanField('I confirm that I am authorized to place this order and that all information provided is accurate', validators=[DataRequired()])
    submit = SubmitField('Place Order')
