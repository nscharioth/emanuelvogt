#!/usr/bin/env python3
"""
Script 22: Add PDF Rotation Table
Creates a table to store user-defined PDF rotations.
"""

import sqlite3

def add_rotation_table(db_path):
    """Add pdf_rotations table to database."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdf_rotations (
            file_id INTEGER PRIMARY KEY,
            rotation INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
    """)
    
    # Create index
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pdf_rotations_file_id 
        ON pdf_rotations(file_id)
    """)
    
    conn.commit()
    
    # Verify
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pdf_rotations'
    """)
    
    if cursor.fetchone():
        print("✅ Table 'pdf_rotations' created successfully")
        
        # Show schema
        cursor.execute("PRAGMA table_info(pdf_rotations)")
        columns = cursor.fetchall()
        print("\nSchema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    else:
        print("❌ Failed to create table")
    
    conn.close()

if __name__ == "__main__":
    db_path = "data/archive.db"
    add_rotation_table(db_path)
