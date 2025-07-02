"""
Migration script to add order lifecycle columns to the chemical_order table.
This adds columns for tracking approval, processing, shipping, and delivery.
"""

import sqlite3
import os

def run_migration():
    """Run the migration to add new columns to chemical_order table"""
    # Get the database path from environment or use default
    db_path = os.environ.get('DATABASE_PATH', 'instance/chemicals.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add columns for order lifecycle tracking
    columns_to_add = [
        ('approved_by', 'INTEGER'),
        ('approved_at', 'TIMESTAMP'),
        ('processed_by', 'INTEGER'),
        ('processed_at', 'TIMESTAMP'),
        ('shipped_by', 'INTEGER'),
        ('shipped_at', 'TIMESTAMP'),
        ('tracking_number', 'TEXT'),
        ('carrier', 'TEXT'),
        ('estimated_delivery', 'TIMESTAMP'),
        ('delivered_at', 'TIMESTAMP'),
        ('received_by', 'INTEGER')
    ]
    
    # Add columns one by one
    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE chemical_order ADD COLUMN {column_name} {column_type}")
            print(f"Added column {column_name} to chemical_order table")
        except sqlite3.OperationalError as e:
            # Column might already exist
            print(f"Note: {e}")
    
    # Add assigned_chemical_id column to order_item table
    try:
        cursor.execute("ALTER TABLE order_item ADD COLUMN assigned_chemical_id INTEGER")
        print("Added assigned_chemical_id column to order_item table")
    except sqlite3.OperationalError as e:
        print(f"Note: {e}")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
