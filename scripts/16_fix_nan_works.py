#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emanuel Vogt Archive - Analyze and Fix "nan" Work IDs
Identifies works with work_number="nan" and provides cleanup options.
"""

import sqlite3
import shutil
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "archive.db"

def create_backup():
    """Create timestamped backup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DATA_DIR / f"archive_backup_{timestamp}.db"
    
    try:
        print(f"[*] Creating backup: {backup_path.name}")
        shutil.copy2(DB_PATH, backup_path)
        print(f"[+] Backup created")
        return True
    except Exception as e:
        print(f"[-] Backup failed: {e}")
        return False

def analyze_nan_works():
    """Find and analyze works with 'nan' work_number."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("=" * 70)
    print("ANALYZING 'nan' WORK IDs")
    print("=" * 70)
    
    # Find nan works
    c.execute("""
        SELECT id, work_number, title, genre
        FROM works 
        WHERE work_number = 'nan' OR work_number LIKE '%nan%'
        ORDER BY id
    """)
    
    nan_works = c.fetchall()
    
    if not nan_works:
        print("\n✅ No works with 'nan' ID found!")
        conn.close()
        return []
    
    print(f"\n[!] Found {len(nan_works)} works with 'nan' ID:\n")
    
    results = []
    for work in nan_works:
        print(f"Work ID {work['id']}: {work['work_number']}")
        print(f"   Title: {work['title']}")
        print(f"   Genre: {work['genre']}")
        
        # Get associated files
        c.execute("""
            SELECT id, filename, filepath
            FROM files 
            WHERE work_id = ?
            ORDER BY filename
        """, (work['id'],))
        
        files = c.fetchall()
        print(f"   Files: {len(files)}")
        
        file_list = []
        for file in files:
            print(f"      - {file['filename']}")
            file_list.append({
                'file_id': file['id'],
                'filename': file['filename'],
                'filepath': file['filepath']
            })
            
            # Try to extract work number from filename
            match = re.match(r'^(\d+|P-\d+)\s*-', file['filename'])
            if match:
                extracted_num = match.group(1)
                print(f"        → Could be Work {extracted_num}")
        
        print()
        
        results.append({
            'work_id': work['id'],
            'work_number': work['work_number'],
            'title': work['title'],
            'genre': work['genre'],
            'files': file_list
        })
    
    conn.close()
    return results

def fix_nan_works(nan_works):
    """Attempt to fix nan works by extracting work numbers from filenames."""
    if not nan_works:
        print("\n[+] No nan works to fix")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("\n" + "=" * 70)
    print("FIXING 'nan' WORKS")
    print("=" * 70)
    
    fixed_count = 0
    orphaned_count = 0
    
    for work_data in nan_works:
        work_id = work_data['work_id']
        files = work_data['files']
        
        if not files:
            print(f"\n[!] Work ID {work_id} has no files - marking for deletion")
            orphaned_count += 1
            continue
        
        # Try to extract work number from first file
        first_file = files[0]
        match = re.match(r'^(\d+|P-\d+)\s*-', first_file['filename'])
        
        if match:
            extracted_num = match.group(1)
            
            # Check if this work number already exists
            c.execute("SELECT id FROM works WHERE work_number = ?", (extracted_num,))
            existing = c.fetchone()
            
            if existing:
                existing_work_id = existing[0]
                print(f"\n[*] Work {extracted_num} already exists (ID {existing_work_id})")
                print(f"    Reassigning {len(files)} files from nan work (ID {work_id})...")
                
                # Reassign files to existing work
                for file in files:
                    c.execute("""
                        UPDATE files 
                        SET work_id = ? 
                        WHERE id = ?
                    """, (existing_work_id, file['file_id']))
                
                # Delete nan work
                c.execute("DELETE FROM works WHERE id = ?", (work_id,))
                fixed_count += 1
                print(f"    ✅ Files reassigned, nan work deleted")
            else:
                # Update work number
                print(f"\n[*] Updating Work ID {work_id} from 'nan' to '{extracted_num}'")
                c.execute("""
                    UPDATE works 
                    SET work_number = ? 
                    WHERE id = ?
                """, (extracted_num, work_id))
                fixed_count += 1
                print(f"    ✅ Work number updated")
        else:
            print(f"\n[!] Could not extract work number from: {first_file['filename']}")
            print(f"    Work ID {work_id} remains as 'nan'")
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "=" * 70)
    print(f"SUMMARY")
    print("=" * 70)
    print(f"   Fixed/reassigned: {fixed_count}")
    print(f"   Orphaned (no files): {orphaned_count}")

def delete_orphaned_works():
    """Delete works that have no associated files."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("\n" + "=" * 70)
    print("DELETING ORPHANED WORKS")
    print("=" * 70)
    
    # Find works with no files
    c.execute("""
        SELECT w.id, w.work_number, w.title
        FROM works w
        LEFT JOIN files f ON w.id = f.work_id
        WHERE f.id IS NULL AND w.work_number = 'nan'
    """)
    
    orphaned = c.fetchall()
    
    if not orphaned:
        print("\n[+] No orphaned 'nan' works found")
        conn.close()
        return
    
    print(f"\n[!] Found {len(orphaned)} orphaned 'nan' works")
    for work_id, work_num, title in orphaned:
        print(f"   Work ID {work_id}: {work_num} - {title}")
    
    response = input(f"\nDelete these {len(orphaned)} orphaned works? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("[-] Cancelled")
        conn.close()
        return
    
    # Delete orphaned works
    for work_id, _, _ in orphaned:
        c.execute("DELETE FROM works WHERE id = ?", (work_id,))
    
    conn.commit()
    print(f"[+] Deleted {len(orphaned)} orphaned works")
    conn.close()

def main():
    print("Emanuel Vogt Archive - Fix 'nan' Work IDs")
    print()
    
    # Step 1: Analyze
    nan_works = analyze_nan_works()
    
    if not nan_works:
        return
    
    # Step 2: Ask user what to do
    print("\n" + "=" * 70)
    print("OPTIONS")
    print("=" * 70)
    print("1. Attempt automatic fix (extract work numbers from filenames)")
    print("2. Delete orphaned works (works with no files)")
    print("3. Manual review (exit without changes)")
    print()
    
    choice = input("Choose option (1/2/3): ").strip()
    
    if choice == "1":
        if not create_backup():
            print("[-] Cannot proceed without backup")
            return
        fix_nan_works(nan_works)
    elif choice == "2":
        if not create_backup():
            print("[-] Cannot proceed without backup")
            return
        delete_orphaned_works()
    else:
        print("\n[*] No changes made. Review the above data manually.")
    
    print("\n" + "=" * 70)
    print("[+] OPERATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
