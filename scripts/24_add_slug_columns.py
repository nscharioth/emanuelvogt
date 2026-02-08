#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emanuel Vogt Archive - Phase 11: Add Slug Columns to Database
Standalone script to add slug-related columns to files table.

Can be run independently before the main reorganization script.
"""

import sqlite3
from pathlib import Path
import sys

# Paths
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "archive.db"


def add_slug_columns():
    """Add new columns to files table for URL-safe file management."""
    
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print(f"Database: {DB_PATH}")
    print()
    
    # Check if columns already exist
    c.execute("PRAGMA table_info(files)")
    columns = [row[1] for row in c.fetchall()]
    
    print("Existing columns in 'files' table:")
    for col in columns:
        print(f"  - {col}")
    print()
    
    # Define new columns
    new_columns = {
        'slug': "ALTER TABLE files ADD COLUMN slug TEXT",
        'flat_path': "ALTER TABLE files ADD COLUMN flat_path TEXT",
        'original_path': "ALTER TABLE files ADD COLUMN original_path TEXT"
    }
    
    # Add missing columns
    added = []
    skipped = []
    
    for col_name, sql in new_columns.items():
        if col_name not in columns:
            try:
                c.execute(sql)
                added.append(col_name)
                print(f"✅ Added column: {col_name}")
            except Exception as e:
                print(f"❌ Error adding {col_name}: {e}")
        else:
            skipped.append(col_name)
            print(f"ℹ️  Column already exists: {col_name}")
    
    # Create index on slug for fast lookups
    if 'slug' in added or 'slug' in columns:
        try:
            c.execute("CREATE INDEX IF NOT EXISTS idx_files_slug ON files(slug)")
            print(f"✅ Created index on 'slug' column")
        except Exception as e:
            print(f"⚠️  Could not create index: {e}")
    
    # Commit changes
    if added:
        conn.commit()
        print(f"\n✅ Successfully added {len(added)} new column(s)")
    else:
        print(f"\nℹ️  No changes needed - all columns already exist")
    
    # Show final schema
    print("\nFinal 'files' table schema:")
    c.execute("PRAGMA table_info(files)")
    for row in c.fetchall():
        col_id, name, col_type, not_null, default, pk = row
        nullable = "NOT NULL" if not_null else "NULL"
        pk_marker = " [PRIMARY KEY]" if pk else ""
        print(f"  {name:20s} {col_type:15s} {nullable:10s}{pk_marker}")
    
    conn.close()


if __name__ == '__main__':
    print("="*70)
    print("EMANUEL VOGT ARCHIVE - ADD SLUG COLUMNS")
    print("="*70)
    print()
    
    try:
        add_slug_columns()
        print("\n" + "="*70)
        print("DONE")
        print("="*70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
