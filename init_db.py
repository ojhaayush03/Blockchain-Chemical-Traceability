from app import create_app, db
from app.models import User, Organization, RoleType
from werkzeug.security import generate_password_hash
from datetime import datetime
import sqlalchemy

app = create_app()
with app.app_context():
    # Create all tables
    db.create_all()
    print("Database tables created successfully.")
    
    # Check if admin organization exists
    admin_org = Organization.query.filter_by(name='System Admin').first()
    if not admin_org:
        admin_org = Organization(
            name='System Admin',
            email_domain='gmail.com',  # Changed to match admin@gmail.com
            description='System Administration',
            created_at=datetime.utcnow(),
            active=True,
            can_manufacture=True,
            can_distribute=True,
            can_receive=True
        )
        db.session.add(admin_org)
        db.session.commit()
        print("Admin organization created successfully.")
    
    # First check if there's any existing admin user
    existing_admin = User.query.filter_by(username='admin').first()
    
    if existing_admin:
        # Update the existing admin user's email and password
        try:
            existing_admin.email = 'admin@gmail.com'
            existing_admin.password_hash = generate_password_hash('Admin@123')
            existing_admin.active = True
            existing_admin.is_admin = True
            existing_admin.role = RoleType.ADMIN
            db.session.commit()
            print("Existing admin user updated with new credentials.")
        except Exception as e:
            print(f"Error updating admin user: {str(e)}")
            db.session.rollback()
    else:
        # No admin user exists, create a new one
        try:
            # Get or create admin organization
            admin_org = Organization.query.filter_by(name='System Admin').first()
            if not admin_org:
                admin_org = Organization(
                    name='System Admin',
                    email_domain='gmail.com',
                    description='System Administration',
                    created_at=datetime.utcnow(),
                    active=True,
                    can_manufacture=True,
                    can_distribute=True,
                    can_receive=True
                )
                db.session.add(admin_org)
                db.session.commit()
            
            admin_user = User(
                username='admin',
                email='admin@gmail.com',
                password_hash=generate_password_hash('Admin@123'),
                first_name='Admin',
                last_name='User',
                role=RoleType.ADMIN,
                organization_id=admin_org.id,
                active=True,
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("New admin user created successfully.")
        except sqlalchemy.exc.IntegrityError as e:
            print(f"Error creating admin user (likely already exists): {str(e)}")
            db.session.rollback()
            
            # Try to update any existing user with admin@gmail.com email
            admin_email_user = User.query.filter_by(email='admin@gmail.com').first()
            if admin_email_user:
                admin_email_user.password_hash = generate_password_hash('Admin@123')
                admin_email_user.active = True
                db.session.commit()
                print("Updated existing user with admin@gmail.com email.")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            db.session.rollback()
    
    print("\nAdmin Login Credentials:")
    print("Email: admin@gmail.com")
    print("Password: Admin@123")
