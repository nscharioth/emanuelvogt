#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Psalm file associations where files like "20 - Psalm 24.pdf" 
are incorrectly assigned to Work 20 instead of Psalm P-20.
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data/archive.db"

def create_backup():
    """Create timestamped backup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BASE_DIR / f"data/archive_backup_{timestamp}.db"
    
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup created: {backup_path.name}")
    return backup_path

def find_misassigned_psalm_files():
    """
    Find files that:
    1. Have filename pattern like "NUMBER - Psalm XX.pdf"
    2. Are assigned to Work with work_number=NUMBER
    3. Should be assigned to Psalm P-NUMBER
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Find files with "Psalm" in filename assigned to regular works (not P-X)
    c.execute("""
        SELECT f.id, f.filename, f.work_id, w.work_number, w.title
        FROM files f
        JOIN works w ON f.work_id = w.id
        WHERE f.filename LIKE '%Psalm%'
        AND w.work_number NOT LIKE 'P-%'
        AND w.work_number NOT LIKE 'nan'
        ORDER BY w.work_number
    """)
    
    misassigned = []
    for file_id, filename, work_id, work_number, work_title in c.fetchall():
        # Check if filename suggests it should be a Psalm work
        # Pattern: "20 - Psalm 24.pdf" should go to P-20
        match = re.match(r'^(\d+[a-z]?)\s*-\s*Psalm\s+(\d+)', filename, re.IGNORECASE)
        if match:
            file_work_num = match.group(1)  # e.g. "20"
            psalm_num = match.group(2)      # e.g. "24"
            
            # If file starts with work_number, it's likely misassigned
            if file_work_num == work_number:
                # Check if corresponding Psalm P-{work_number} exists
                c.execute("SELECT id, title FROM works WHERE work_number = ?", (f"P-{work_number}",))
                psalm_work = c.fetchone()
                
                if psalm_work:
                    misassigned.append({
                        'file_id': file_id,
                        'filename': filename,
                        'current_work_id': work_id,
                        'current_work_number': work_number,
                        'current_work_title': work_title,
                        'correct_work_id': psalm_work[0],
                        'correct_work_number': f"P-{work_number}",
                        'correct_work_title': psalm_work[1]
                    })
    
    conn.close()
    return misassigned

def fix_associations(misassigned, auto_fix=False):
    """Fix file associations."""
    if not misassigned:
        print("✅ No misassigned Psalm files found!")
        return
    
    print(f"\n{'='*80}")
    print(f"Found {len(misassigned)} misassigned Psalm files:")
    print(f"{'='*80}\n")
    
    for item in misassigned:
        print(f"File: {item['filename']}")
        print(f"  Currently assigned to:")
        print(f"    Work {item['current_work_number']} (ID {item['current_work_id']}): {item['current_work_title']}")
        print(f"  Should be assigned to:")
        print(f"    Psalm {item['correct_work_number']} (ID {item['correct_work_id']}): {item['correct_work_title']}")
        print()
    
    if not auto_fix:
        response = input(f"\nFix these {len(misassigned)} file associations? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Aborted.")
            return
    
    # Apply fixes
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    fixed = 0
    for item in misassigned:
        c.execute("""
            UPDATE files 
            SET work_id = ? 
            WHERE id = ?
        """, (item['correct_work_id'], item['file_id']))
        fixed += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Fixed {fixed} file associations!")

def verify_fix():
    """Verify no more misassigned files."""
    misassigned = find_misassigned_psalm_files()
    if not misassigned:
        print("\n✅ VERIFICATION PASSED: No misassigned Psalm files remain.")
    else:
        print(f"\n⚠️  WARNING: Still {len(misassigned)} misassigned files found!")

def main():
    print("=" * 80)
    print("FIX PSALM FILE ASSOCIATIONS")
    print("=" * 80)
    print("\nThis script fixes files like '20 - Psalm 24.pdf' that are")
    print("incorrectly assigned to Work 20 instead of Psalm P-20.\n")
    
    # Analyze
    misassigned = find_misassigned_psalm_files()
    
    if not misassigned:
        print("✅ No misassigned Psalm files found! Database is correct.")
        return
    
    # Create backup
    create_backup()
    
    # Fix
    fix_associations(misassigned, auto_fix=False)
    
    # Verify
    verify_fix()

if __name__ == "__main__":
    main()
