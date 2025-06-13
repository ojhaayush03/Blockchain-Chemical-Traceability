"""
Database reset script - drops all tables and recreates them with RBAC support
This will completely erase all data in the database and set up initial admin user
"""
from app import create_app, db
from app.models import create_admin_user
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the application context
app = create_app()

with app.app_context():
    # Check if the database file exists and print its path
    db_path = os.path.join(app.instance_path, 'chemicals.db')
    if os.path.exists(db_path):
        logger.info(f"Found database at: {db_path}")
        print(f"Found database at: {db_path}")
    else:
        logger.info(f"Database file not found at: {db_path}, will create new database.")
        print(f"Database file not found at: {db_path}, will create new database.")
    
    # Drop all tables
    print("Dropping all tables...")
    db.drop_all()
    print("All tables have been dropped.")
    
    # Recreate all tables
    print("Creating new tables with updated schema...")
    db.create_all()
    print("Database tables recreated successfully.")
    
    # Create the admin user
    print("Setting up initial admin user...")
    admin_user, created = create_admin_user(db.session)
    if created:
        print(f"Created admin user: {admin_user.username} ({admin_user.email})")
        print("Default password: Admin@123 - Please change this immediately after first login!")
    else:
        print(f"Admin user already existed: {admin_user.username} ({admin_user.email})")
    
    
    # Create allowed locations list (for validation)
    print("\nSetting up predefined validation rules...")
    # Locations could be stored in a configuration table in a real application
    
    # Print summary of what happened
    print("\nDatabase has been reset successfully with RBAC support.")
    print("You can now use the system with the following roles:")
    
    print("1. ADMIN: Platform provider - can manage organizations")
    
    print("2. MANUFACTURER: Can register chemicals from authorized organizations")
    
    print("3. DISTRIBUTOR: Can log movements of chemicals")
    
    print("4. CUSTOMER: Can receive and confirm chemical deliveries")
    
    print("\nInitial admin credentials:")
    
    print("  Username: admin")
    
    print("  Email: admin@gmail.com")
    
    print("  Password: Admin@123")
    
    print("\nIMPORTANT: Change the default admin password after first login!")
    

print("Database reset complete with RBAC implementation.")

