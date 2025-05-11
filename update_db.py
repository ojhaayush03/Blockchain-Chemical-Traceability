from app import create_app
import sqlite3
import os

app = create_app()

def column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def update_database_schema():
    with app.app_context():
        # Get the path to the database file
        db_path = os.path.join(app.instance_path, 'chemicals.db')
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if movement_log table exists and has correct structure
            if table_exists(cursor, 'movement_log'):
                # Check if location column exists
                if not column_exists(cursor, 'movement_log', 'location'):
                    print("Movement log table exists but missing 'location' column. Recreating table...")
                    
                    # Get existing data
                    cursor.execute("SELECT id, tag_id, timestamp, moved_by, purpose, status, remarks FROM movement_log")
                    existing_data = cursor.fetchall()
                    
                    # Drop and recreate table
                    cursor.execute("DROP TABLE movement_log")
                    
                    # Create table with correct structure
                    cursor.execute("""
                    CREATE TABLE movement_log (
                        id INTEGER PRIMARY KEY,
                        tag_id TEXT NOT NULL,
                        location TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        moved_by TEXT,
                        purpose TEXT,
                        status TEXT,
                        remarks TEXT
                    )
                    """)
                    
                    # Reinsert data with default location
                    for row in existing_data:
                        id, tag_id, timestamp, moved_by, purpose, status, remarks = row
                        cursor.execute("""
                        INSERT INTO movement_log (id, tag_id, location, timestamp, moved_by, purpose, status, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (id, tag_id, "Unknown", timestamp, moved_by, purpose, status, remarks))
                    
                    print("Movement log table recreated with 'location' column")
            
            # Chemical table columns to add
            chemical_columns = [
                ('manufacturer', 'TEXT'),
                ('quantity', 'FLOAT'),
                ('unit', 'TEXT'),
                ('expiry_date', 'DATE'),
                ('storage_condition', 'TEXT'),
                ('received_date', 'DATE'),
                ('batch_number', 'TEXT'),
                ('hazard_class', 'TEXT'),
                ('cas_number', 'TEXT'),
                ('description', 'TEXT'),
                ('current_location', 'TEXT NOT NULL DEFAULT "Storage"')
            ]
            
            # MovementLog table columns to add
            movement_columns = [
                ('moved_by', 'TEXT'),
                ('purpose', 'TEXT'),
                ('status', 'TEXT'),
                ('remarks', 'TEXT')
            ]
            
            # Add columns to Chemical table if they don't exist
            for col_name, col_type in chemical_columns:
                if not column_exists(cursor, 'chemical', col_name):
                    cursor.execute(f'ALTER TABLE chemical ADD COLUMN {col_name} {col_type}')
                    print(f"Added column {col_name} to chemical table")
            
            # Add columns to MovementLog table if they don't exist
            for col_name, col_type in movement_columns:
                if not column_exists(cursor, 'movement_log', col_name):
                    cursor.execute(f'ALTER TABLE movement_log ADD COLUMN {col_name} {col_type}')
                    print(f"Added column {col_name} to movement_log table")
            
            conn.commit()
            print("Database schema update completed!")
        except sqlite3.OperationalError as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    update_database_schema()
