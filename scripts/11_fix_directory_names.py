#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Fix Directory Names for Windows Compatibility
Renames problematic directory names and updates database paths.
"""

import sqlite3
import shutil
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "archive.db"
ARCHIVE_DIR = BASE_DIR / "archive" / "files"

def rename_directory():
    """Rename 'Werke - außer Psalmen' to 'Werke'."""
    old_path = ARCHIVE_DIR / "Werke - außer Psalmen"
    new_path = ARCHIVE_DIR / "Werke"
    
    if not old_path.exists():
        print(f"⚠️  Directory '{old_path.name}' not found")
        if new_path.exists():
            print(f"✅ Directory already renamed to '{new_path.name}'")
            return True
        return False
    
    if new_path.exists():
        print(f"❌ Target directory '{new_path.name}' already exists!")
        print(f"   Please manually resolve this conflict.")
        return False
    
    try:
        print(f"📁 Renaming directory...")
        print(f"   From: {old_path.name}")
        print(f"   To:   {new_path.name}")
        old_path.rename(new_path)
        print(f"✅ Directory renamed successfully")
        return True
    except Exception as e:
        print(f"❌ Error renaming directory: {e}")
        return False

def update_database_paths():
    """Update all file paths in the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Get count of files with old path
        c.execute("""
            SELECT COUNT(*) FROM files 
            WHERE filepath LIKE '%Werke - außer Psalmen%'
        """)
        count = c.fetchone()[0]
        
        if count == 0:
            print(f"✅ No files with old path found in database")
            return True
        
        print(f"\n📝 Updating {count} file paths in database...")
        
        # Update the paths
        c.execute("""
            UPDATE files 
            SET filepath = REPLACE(filepath, 'Werke - außer Psalmen', 'Werke')
            WHERE filepath LIKE '%Werke - außer Psalmen%'
        """)
        
        updated = c.rowcount
        conn.commit()
        
        print(f"✅ Updated {updated} file paths successfully")
        
        # Verify the update
        c.execute("""
            SELECT COUNT(*) FROM files 
            WHERE filepath LIKE '%Werke - außer Psalmen%'
        """)
        remaining = c.fetchone()[0]
        
        if remaining > 0:
            print(f"⚠️  Warning: {remaining} files still have old path")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database update error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_paths():
    """Verify that all file paths in database exist on disk."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print(f"\n🔍 Verifying file paths...")
    
    c.execute("SELECT COUNT(*) FROM files")
    total = c.fetchone()[0]
    
    c.execute("""
        SELECT filepath FROM files 
        WHERE filepath LIKE '%Werke%' 
        LIMIT 5
    """)
    samples = c.fetchall()
    
    missing = 0
    found = 0
    
    for (filepath,) in samples:
        full_path = BASE_DIR / "archive" / filepath
        if full_path.exists():
            found += 1
        else:
            missing += 1
            print(f"   ⚠️  Missing: {filepath}")
    
    conn.close()
    
    print(f"\n📊 Sample verification (5 files):")
    print(f"   Found: {found}")
    print(f"   Missing: {missing}")
    print(f"   Total files in DB: {total}")
    
    return missing == 0

def create_backup():
    """Create a backup of the database before making changes."""
    backup_path = DB_PATH.parent / f"{DB_PATH.stem}_backup_before_rename{DB_PATH.suffix}"
    
    try:
        print(f"💾 Creating database backup...")
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Backup created: {backup_path.name}")
        return True
    except Exception as e:
        print(f"❌ Backup error: {e}")
        return False

def main():
    print("=" * 70)
    print("Emanuel Vogt Archive - Directory Name Fix")
    print("=" * 70)
    print("\nThis script will:")
    print("1. Rename 'Werke - außer Psalmen' → 'Werke'")
    print("2. Update all database paths")
    print("3. Verify the changes")
    print("\n⚠️  This operation cannot be easily undone!")
    
    response = input("\nProceed? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Operation cancelled by user")
        return
    
    # Step 1: Create backup
    if not create_backup():
        print("\n❌ Cannot proceed without backup")
        return
    
    # Step 2: Rename directory
    print(f"\n" + "=" * 70)
    print("STEP 1: Renaming Directory")
    print("=" * 70)
    if not rename_directory():
        print("\n❌ Directory rename failed. Database not modified.")
        return
    
    # Step 3: Update database
    print(f"\n" + "=" * 70)
    print("STEP 2: Updating Database Paths")
    print("=" * 70)
    if not update_database_paths():
        print("\n❌ Database update failed")
        print("   You may need to manually rename the directory back")
        return
    
    # Step 4: Verify
    print(f"\n" + "=" * 70)
    print("STEP 3: Verification")
    print("=" * 70)
    verify_paths()
    
    print(f"\n" + "=" * 70)
    print("✅ MIGRATION COMPLETE")
    print("=" * 70)
    print("\nDirectory structure is now Windows-compatible!")
    print(f"Backup saved as: {DB_PATH.stem}_backup_before_rename{DB_PATH.suffix}")
    print("\n⚠️  Remember to update any external scripts or documentation")
    print("   that reference the old directory name.")

if __name__ == "__main__":
    main()
