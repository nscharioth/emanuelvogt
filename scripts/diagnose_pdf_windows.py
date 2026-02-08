#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows PDF Path Diagnostic Tool
Diagnose why PDFs return 404 on Windows but work on macOS.

Updated for Phase 11: Now checks both old (files/) and new (flat/) archive structures.
"""

import sqlite3
import sys
from pathlib import Path
import os

# Determine base directory
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DB_PATH = BASE_DIR / "data" / "archive.db"
ARCHIVE_DIR = BASE_DIR / "archive"
OLD_ARCHIVE = ARCHIVE_DIR / "files"
NEW_ARCHIVE = ARCHIVE_DIR / "flat"

print("=" * 70)
print("PDF PATH DIAGNOSTIC - Work ID 3 (Phase 11 Enhanced)")
print("=" * 70)
print()

# Check database exists
if not DB_PATH.exists():
    print(f"❌ Database not found: {DB_PATH}")
    sys.exit(1)

print(f"✅ Database found: {DB_PATH}")
print(f"📁 Old archive (files/): {OLD_ARCHIVE}")
print(f"   Exists: {OLD_ARCHIVE.exists()}")
print(f"📁 New archive (flat/): {NEW_ARCHIVE}")
print(f"   Exists: {NEW_ARCHIVE.exists()}")
print()

# Connect to database
conn = sqlite3.connect(DB_PATH)
conn.text_factory = lambda x: x.decode('utf-8', errors='replace')
c = conn.cursor()

# Get Work 3 details
print("=" * 70)
print("WORK 3 DETAILS")
print("=" * 70)

c.execute("SELECT id, work_number, title FROM works WHERE id = 3")
work = c.fetchone()
if work:
    print(f"Work ID: {work[0]}")
    print(f"Work Number: {work[1]}")
    print(f"Title: {work[2]}")
else:
    print("❌ Work 3 not found in database!")
    conn.close()
    sys.exit(1)

print()

# Get files for Work 3
print("=" * 70)
print("FILES FOR WORK 3")
print("=" * 70)

c.execute("""
    SELECT id, filename, filepath, file_type, size_bytes, slug, flat_path, original_path
    FROM files
    WHERE work_id = 3
""")

files = c.fetchall()
print(f"Found {len(files)} file(s):")
print()

for row in files:
    file_id = row[0]
    filename = row[1]
    filepath = row[2]
    file_type = row[3]
    size_bytes = row[4]
    slug = row[5] if len(row) > 5 else None
    flat_path = row[6] if len(row) > 6 else None
    original_path = row[7] if len(row) > 7 else None
    
    print(f"File ID: {file_id}")
    print(f"  Filename: {filename}")
    print(f"  Database path (current): {repr(filepath)}")
    if original_path:
        print(f"  Database path (original): {repr(original_path)}")
    if slug:
        print(f"  Slug (URL-safe): {slug}")
    if flat_path:
        print(f"  Flat path: {flat_path}")
    print(f"  File type: {file_type}")
    print(f"  Size: {size_bytes / 1024 / 1024:.2f} MB")
    print()
    
    # Test path resolution - Phase 11 Hybrid approach
    print("  Path Resolution Tests (Phase 11 Hybrid):")
    
    # Strategy 1: Flat archive (preferred)
    if flat_path:
        flat_full = ARCHIVE_DIR / flat_path
        print(f"    Strategy 1 (flat/):")
        print(f"      Path: {flat_full}")
        print(f"      Exists: {flat_full.exists()}")
    else:
        print(f"    Strategy 1 (flat/): Not available (no slug)")
    
    # Strategy 2: Old archive with normalized separators
    filepath_normalized = filepath.replace('/', os.sep)
    old_full = OLD_ARCHIVE / filepath_normalized
    print(f"    Strategy 2 (files/ normalized):")
    print(f"      Path: {old_full}")
    print(f"      Exists: {old_full.exists()}")
    
    # Strategy 3: Old archive direct
    old_direct = OLD_ARCHIVE / filepath
    print(f"    Strategy 3 (files/ direct):")
    print(f"      Path: {old_direct}")
    print(f"      Exists: {old_direct.exists()}")
    
    # Try to list what's actually in the directory
    expected_dir = old_full.parent
    print(f"    Expected directory: {expected_dir}")
    print(f"      Directory exists: {expected_dir.exists()}")
    
    if expected_dir.exists():
        try:
            files_in_dir = list(expected_dir.glob('*.pdf'))
            print(f"      PDF files in directory: {len(files_in_dir)}")
            if files_in_dir:
                print(f"      Files matching '14a*':")
                matching = [f for f in files_in_dir if f.name.startswith('14a')]
                if matching:
                    for f in matching:
                        print(f"        - {f.name}")
                else:
                    print(f"        (no files starting with '14a' found)")
                
                # Look for similar names
                print(f"      Looking for similar names (Hör):")
                similar = [f for f in files_in_dir if 'hör' in f.name.lower() or '14' in f.name.lower()]
                for f in similar[:5]:
                    print(f"        - {f.name}")
        except Exception as e:
            print(f"      Error listing directory: {e}")
    
    print()

conn.close()

print("=" * 70)
print("REORGANIZATION STATUS")
print("=" * 70)
print()

if NEW_ARCHIVE.exists():
    try:
        flat_files = list(NEW_ARCHIVE.glob('*.*'))
        print(f"✅ Flat archive exists with {len(flat_files)} files")
        if flat_files:
            print("   Sample files:")
            for f in flat_files[:5]:
                print(f"     - {f.name}")
    except Exception as e:
        print(f"⚠️  Error reading flat archive: {e}")
else:
    print("ℹ️  Flat archive not yet created")
    print("   Run: python scripts/23_reorganize_archive.py --live")

print()
print("=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
print()
print("Please send this output for analysis.")
print()
print("If flat/ archive doesn't exist yet, run:")
print("  python scripts/23_reorganize_archive.py --live --limit=10  # Test")
print("  python scripts/23_reorganize_archive.py --live              # Full")

