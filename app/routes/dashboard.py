from flask import Blueprint, render_template
from app.extensions import db
from app.models import Chemical  # Adjust this if your model import is different

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    chemicals = Chemical.query.all()
    return render_template('dashboard.html', chemicals=chemicals)
