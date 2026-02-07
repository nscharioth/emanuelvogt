#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emanuel Vogt Archive - Fix File-to-Work Associations
Corrects files that were incorrectly associated with works due to partial number matches.
"""

import sqlite3
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "archive.db"

def extract_work_number_from_filename(filename):
    """
    Extract the primary work number from a filename.
    Only matches work numbers at the START of the filename.
    """
    # Match pattern: "NUMBER - Title"
    # Examples: "4 - Title.pdf", "126 - Title.pdf", "P-19 - Title.pdf"
    match = re.match(r'^(\d+|P-\d+)\s*-\s*', filename)
    if match:
        return match.group(1)
    return None

def get_work_id_by_number(conn, work_number):
    """Get work ID by work number."""
    c = conn.cursor()
    c.execute("SELECT id FROM works WHERE work_number = ?", (work_number,))
    result = c.fetchone()
    return result[0] if result else None

def fix_file_associations():
    """Fix incorrect file-to-work associations."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all files
    c.execute("SELECT id, filename, filepath, work_id FROM files")
    all_files = c.fetchall()
    
    fixes = []
    errors = []
    
    print(f"[*] Analyzing {len(all_files)} files...")
    
    for file_id, filename, filepath, current_work_id in all_files:
        # Extract the correct work number from filename
        correct_work_number = extract_work_number_from_filename(filename)
        
        if not correct_work_number:
            # No work number in filename, skip
            continue
        
        # Get the correct work_id
        correct_work_id = get_work_id_by_number(conn, correct_work_number)
        
        if not correct_work_id:
            errors.append(f"Work {correct_work_number} not found for file: {filename}")
            continue
        
        # Check if association is wrong
        if current_work_id != correct_work_id:
            fixes.append({
                'file_id': file_id,
                'filename': filename,
                'old_work_id': current_work_id,
                'new_work_id': correct_work_id,
                'work_number': correct_work_number
            })
    
    print(f"\n[*] Analysis complete:")
    print(f"   Total files: {len(all_files)}")
    print(f"   Incorrect associations: {len(fixes)}")
    print(f"   Errors: {len(errors)}")
    
    if errors:
        print(f"\n[!] Errors found:")
        for error in errors[:10]:  # Show first 10
            print(f"   {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more")
    
    if not fixes:
        print(f"\n[+] No incorrect associations found!")
        conn.close()
        return
    
    print(f"\n[*] Examples of fixes needed:")
    for fix in fixes[:5]:  # Show first 5 examples
        print(f"   {fix['filename']}")
        print(f"      Old work_id: {fix['old_work_id']} -> New work_id: {fix['new_work_id']} (Work {fix['work_number']})")
    
    response = input(f"\nApply {len(fixes)} fixes? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("[-] Operation cancelled")
        conn.close()
        return
    
    # Apply fixes
    print(f"\n[*] Applying fixes...")
    for fix in fixes:
        c.execute("""
            UPDATE files 
            SET work_id = ? 
            WHERE id = ?
        """, (fix['new_work_id'], fix['file_id']))
    
    conn.commit()
    print(f"[+] Fixed {len(fixes)} file associations")
    
    # Verify the fix for work 4
    c.execute("""
        SELECT filename FROM files WHERE work_id = (
            SELECT id FROM works WHERE work_number = '4'
        )
    """)
    work_4_files = c.fetchall()
    
    print(f"\n[*] Verification: Work 4 now has {len(work_4_files)} file(s):")
    for (filename,) in work_4_files:
        print(f"   - {filename}")
    
    conn.close()

def main():
    print("=" * 70)
    print("Emanuel Vogt Archive - Fix File-Work Associations")
    print("=" * 70)
    print("\nThis script will:")
    print("1. Analyze all file-to-work associations")
    print("2. Identify files incorrectly associated based on partial number matches")
    print("3. Reassociate files to correct works based on filename prefix")
    print()
    
    try:
        fix_file_associations()
        print("\n" + "=" * 70)
        print("[+] OPERATION COMPLETE")
        print("=" * 70)
    except Exception as e:
        print(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
