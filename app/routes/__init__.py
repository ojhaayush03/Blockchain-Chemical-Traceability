from app.routes.dashboard import dashboard_bp
from app.routes.main import main  # This imports the `main` blueprint from `main.py`
from app.routes.auth import auth_bp  # Import the auth blueprint
from app.routes.admin import admin_bp  # Import the admin blueprint
from app.routes.distributor import distributor_bp  # Import the distributor blueprint
from app.routes.customer import customer_bp  # Import the customer blueprint
from app.routes.manufacturer import manufacturer_bp  # Import the manufacturer blueprint

# Specify public API
__all__ = ['dashboard_bp', 'main', 'auth_bp', 'admin_bp', 'distributor_bp', 'customer_bp', 'manufacturer_bp']
