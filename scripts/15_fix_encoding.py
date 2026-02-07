#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emanuel Vogt Archive - Fix Windows Encoding for Umlauts
Fixes database text encoding to properly display German characters (ä,ö,ü,ß) on Windows.
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "archive.db"

def create_backup():
    """Create timestamped backup of database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DATA_DIR / f"archive_backup_{timestamp}.db"
    
    try:
        print(f"[*] Creating backup: {backup_path.name}")
        shutil.copy2(DB_PATH, backup_path)
        print(f"[+] Backup created successfully")
        return True
    except Exception as e:
        print(f"[-] Backup failed: {e}")
        return False

def analyze_encoding_issues():
    """Analyze database for encoding problems."""
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = bytes  # Get raw bytes
    c = conn.cursor()
    
    print("\n[*] Analyzing encoding issues...")
    
    # Check works table
    c.execute("SELECT id, work_number, title FROM works LIMIT 100")
    works_issues = 0
    for work_id, work_num_bytes, title_bytes in c.fetchall():
        try:
            title_bytes.decode('utf-8')
        except UnicodeDecodeError:
            works_issues += 1
            if works_issues <= 3:  # Show first 3 examples
                print(f"   Work {work_id}: {title_bytes[:50]}...")
    
    # Check files table
    c.execute("SELECT id, filename, filepath FROM files LIMIT 100")
    files_issues = 0
    for file_id, filename_bytes, filepath_bytes in c.fetchall():
        try:
            filename_bytes.decode('utf-8')
            filepath_bytes.decode('utf-8')
        except UnicodeDecodeError:
            files_issues += 1
            if files_issues <= 3:  # Show first 3 examples
                print(f"   File {file_id}: {filename_bytes[:50]}...")
    
    conn.close()
    
    print(f"\n[*] Analysis Results:")
    print(f"   Works with encoding issues: {works_issues}/100 sampled")
    print(f"   Files with encoding issues: {files_issues}/100 sampled")
    
    return works_issues > 0 or files_issues > 0

def fix_encoding():
    """Fix encoding in database tables."""
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = bytes  # Get raw bytes
    c = conn.cursor()
    
    print("\n[*] Fixing encoding in works table...")
    
    # Fix works table
    c.execute("SELECT id, work_number, title, sort_title, genre, instrumentation FROM works")
    works_rows = c.fetchall()
    
    works_fixed = 0
    for row in works_rows:
        work_id = row[0]
        fixed_values = []
        needs_fix = False
        
        for value in row[1:]:  # Skip id
            if value is None:
                fixed_values.append(None)
                continue
            
            if isinstance(value, bytes):
                # Try multiple encodings
                decoded = None
                for encoding in ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1252']:
                    try:
                        decoded = value.decode(encoding)
                        if encoding != 'utf-8':
                            needs_fix = True
                        break
                    except:
                        continue
                
                if decoded is None:
                    decoded = value.decode('utf-8', errors='replace')
                    needs_fix = True
                
                fixed_values.append(decoded)
            else:
                fixed_values.append(str(value) if value else None)
        
        if needs_fix:
            c.execute("""
                UPDATE works 
                SET work_number = ?, title = ?, sort_title = ?, genre = ?, instrumentation = ?
                WHERE id = ?
            """, (*fixed_values, work_id))
            works_fixed += 1
    
    print(f"[+] Fixed {works_fixed} works")
    
    # Fix files table
    print("\n[*] Fixing encoding in files table...")
    
    c.execute("SELECT id, filename, filepath FROM files")
    files_rows = c.fetchall()
    
    files_fixed = 0
    for file_id, filename_bytes, filepath_bytes in files_rows:
        needs_fix = False
        
        # Fix filename
        if isinstance(filename_bytes, bytes):
            filename_fixed = None
            for encoding in ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1252']:
                try:
                    filename_fixed = filename_bytes.decode(encoding)
                    if encoding != 'utf-8':
                        needs_fix = True
                    break
                except:
                    continue
            
            if filename_fixed is None:
                filename_fixed = filename_bytes.decode('utf-8', errors='replace')
                needs_fix = True
        else:
            filename_fixed = str(filename_bytes) if filename_bytes else ""
        
        # Fix filepath
        if isinstance(filepath_bytes, bytes):
            filepath_fixed = None
            for encoding in ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1252']:
                try:
                    filepath_fixed = filepath_bytes.decode(encoding)
                    if encoding != 'utf-8':
                        needs_fix = True
                    break
                except:
                    continue
            
            if filepath_fixed is None:
                filepath_fixed = filepath_bytes.decode('utf-8', errors='replace')
                needs_fix = True
        else:
            filepath_fixed = str(filepath_bytes) if filepath_bytes else ""
        
        if needs_fix:
            c.execute("""
                UPDATE files 
                SET filename = ?, filepath = ?
                WHERE id = ?
            """, (filename_fixed, filepath_fixed, file_id))
            files_fixed += 1
    
    conn.commit()
    print(f"[+] Fixed {files_fixed} files")
    
    conn.close()
    
    return works_fixed, files_fixed

def verify_fix():
    """Verify that encoding issues are resolved."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("\n[*] Verifying fixes...")
    
    # Test with known problematic characters
    test_chars = ['ä', 'ö', 'ü', 'ß', 'Ä', 'Ö', 'Ü']
    
    # Check works
    c.execute("""
        SELECT work_number, title 
        FROM works 
        WHERE title LIKE '%ä%' OR title LIKE '%ö%' OR title LIKE '%ü%' OR title LIKE '%ß%'
        LIMIT 5
    """)
    
    works_with_umlauts = c.fetchall()
    
    if works_with_umlauts:
        print(f"\n[+] Found {len(works_with_umlauts)} works with umlauts (sample):")
        for work in works_with_umlauts:
            print(f"   {work['work_number']}: {work['title']}")
    
    # Check files
    c.execute("""
        SELECT filename 
        FROM files 
        WHERE filename LIKE '%ä%' OR filename LIKE '%ö%' OR filename LIKE '%ü%' OR filename LIKE '%ß%'
        LIMIT 5
    """)
    
    files_with_umlauts = c.fetchall()
    
    if files_with_umlauts:
        print(f"\n[+] Found {len(files_with_umlauts)} files with umlauts (sample):")
        for file in files_with_umlauts:
            print(f"   {file['filename']}")
    
    conn.close()
    
    return True

def update_backend_encoding():
    """Provide instructions for backend.py update."""
    print("\n" + "=" * 70)
    print("MANUAL STEP REQUIRED: Update backend.py")
    print("=" * 70)
    print("""
Add the following smart text factory to backend.py after database connection:

# In backend.py, after "conn = sqlite3.connect(DB_PATH)"
def smart_text_factory(data):
    '''Smart decoding that handles multiple encodings.'''
    if isinstance(data, bytes):
        for encoding in ['utf-8', 'windows-1252', 'iso-8859-1']:
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, AttributeError):
                continue
        return data.decode('utf-8', errors='replace')
    return str(data)

conn.text_factory = smart_text_factory

This ensures the backend can handle any remaining encoding variations.
""")

def main():
    print("=" * 70)
    print("Emanuel Vogt Archive - Windows Encoding Fix")
    print("=" * 70)
    print()
    print("This script will:")
    print("1. Create a backup of the database")
    print("2. Analyze encoding issues")
    print("3. Fix text encoding to UTF-8 (from Windows-1252/ISO-8859-1)")
    print("4. Verify the fixes")
    print()
    
    response = input("Proceed? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("[-] Operation cancelled")
        return
    
    # Step 1: Backup
    if not create_backup():
        print("[-] Cannot proceed without backup")
        return
    
    # Step 2: Analyze
    has_issues = analyze_encoding_issues()
    
    if not has_issues:
        print("\n[+] No encoding issues detected!")
        print("    Database already uses proper UTF-8 encoding")
        verify_fix()
        return
    
    # Step 3: Fix
    print("\n" + "=" * 70)
    print("FIXING ENCODING")
    print("=" * 70)
    
    works_fixed, files_fixed = fix_encoding()
    
    print(f"\n[+] Encoding fix complete!")
    print(f"   Works fixed: {works_fixed}")
    print(f"   Files fixed: {files_fixed}")
    
    # Step 4: Verify
    verify_fix()
    
    # Step 5: Backend update instructions
    update_backend_encoding()
    
    print("\n" + "=" * 70)
    print("[+] OPERATION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Update backend.py with smart text factory (see above)")
    print("2. Test on Windows machine with umlaut filenames")
    print("3. Verify PDF viewer displays names correctly")

if __name__ == "__main__":
    main()
