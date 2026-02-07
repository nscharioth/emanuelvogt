#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emanuel Vogt Archive - Analyze Psalm ID Collision Issue
Investigates whether Psalms and Works actually collide in the PDF viewer.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "archive.db"

def analyze_id_structure():
    """Analyze how IDs are structured in the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("=" * 70)
    print("ANALYZING ID STRUCTURE")
    print("=" * 70)
    
    # Check works table
    c.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(id) as min_id,
            MAX(id) as max_id
        FROM works
    """)
    works_stats = c.fetchone()
    
    print(f"\n[*] Works Table:")
    print(f"   Total works: {works_stats['total']}")
    print(f"   ID range: {works_stats['min_id']} - {works_stats['max_id']}")
    
    # Count Psalms vs regular works
    c.execute("SELECT COUNT(*) FROM works WHERE work_number LIKE 'P-%'")
    psalm_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM works WHERE work_number NOT LIKE 'P-%'")
    regular_count = c.fetchone()[0]
    
    print(f"\n   Psalms (P-X): {psalm_count}")
    print(f"   Regular works: {regular_count}")
    
    # Show sample Psalm IDs
    c.execute("""
        SELECT id, work_number, title 
        FROM works 
        WHERE work_number LIKE 'P-%' 
        ORDER BY id 
        LIMIT 10
    """)
    
    print(f"\n   Sample Psalm works:")
    for work in c.fetchall():
        print(f"      ID {work['id']}: {work['work_number']} - {work['title'][:50]}")
    
    # Show sample regular works with similar IDs
    c.execute("""
        SELECT id, work_number, title 
        FROM works 
        WHERE work_number NOT LIKE 'P-%' 
        AND CAST(work_number AS INTEGER) <= 10
        ORDER BY CAST(work_number AS INTEGER)
        LIMIT 10
    """)
    
    print(f"\n   Sample regular works (1-10):")
    for work in c.fetchall():
        print(f"      ID {work['id']}: Work {work['work_number']} - {work['title'][:50]}")
    
    conn.close()

def check_viewer_collision():
    """Check if the viewer actually has collision issues."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("\n" + "=" * 70)
    print("CHECKING FOR ACTUAL COLLISIONS")
    print("=" * 70)
    
    # The viewer uses work_id to fetch files, not work_number
    # So P-1 and Work 1 have different work_id values
    
    # Find Psalm P-1
    c.execute("SELECT id, work_number, title FROM works WHERE work_number = 'P-1'")
    psalm_1 = c.fetchone()
    
    if psalm_1:
        print(f"\n[*] Psalm P-1:")
        print(f"   Database ID (work_id): {psalm_1['id']}")
        print(f"   Title: {psalm_1['title']}")
        
        # Get files for this work
        c.execute("SELECT COUNT(*), filename FROM files WHERE work_id = ? LIMIT 1", (psalm_1['id'],))
        file_info = c.fetchone()
        if file_info and file_info[0] > 0:
            print(f"   Files: {file_info[0]}")
            print(f"   Sample: {file_info[1]}")
    else:
        print("\n[!] Psalm P-1 not found in database")
    
    # Find regular Work 1
    c.execute("SELECT id, work_number, title FROM works WHERE work_number = '1'")
    work_1 = c.fetchone()
    
    if work_1:
        print(f"\n[*] Work 1:")
        print(f"   Database ID (work_id): {work_1['id']}")
        print(f"   Title: {work_1['title']}")
        
        # Get files for this work
        c.execute("SELECT COUNT(*), filename FROM files WHERE work_id = ? LIMIT 1", (work_1['id'],))
        file_info = c.fetchone()
        if file_info and file_info[0] > 0:
            print(f"   Files: {file_info[0]}")
            print(f"   Sample: {file_info[1]}")
    else:
        print("\n[!] Work 1 not found in database")
    
    # Check if they have different database IDs
    if psalm_1 and work_1:
        if psalm_1['id'] == work_1['id']:
            print(f"\n⚠️  COLLISION DETECTED!")
            print(f"   Psalm P-1 and Work 1 share the same database ID: {psalm_1['id']}")
            print(f"   This WILL cause PDF merging in the viewer!")
            return True
        else:
            print(f"\n✅ NO COLLISION")
            print(f"   Psalm P-1 (ID {psalm_1['id']}) and Work 1 (ID {work_1['id']}) have different database IDs")
            print(f"   The viewer should display them separately.")
            return False
    
    conn.close()
    return False

def check_frontend_logic():
    """Analyze how the frontend handles work IDs."""
    print("\n" + "=" * 70)
    print("FRONTEND LOGIC ANALYSIS")
    print("=" * 70)
    
    app_js_path = BASE_DIR / "app/static/app.js"
    backend_path = BASE_DIR / "app/backend.py"
    
    print("\n[*] Checking app.js...")
    
    with open(app_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check if work_id or id is used
        if 'work.id' in content:
            print("   ✅ Uses work.id (database ID) - Correct!")
        
        if 'work.work_number' in content:
            print("   ℹ️  Also uses work.work_number (P-1, 1, etc.)")
    
    print("\n[*] Checking backend.py...")
    
    with open(backend_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check PDF endpoint
        if '@app.get("/pdf/{file_id}")' in content:
            print("   ✅ PDF endpoint uses file_id - Correct!")
        
        # Check work detail endpoint
        if '@app.get("/api/work/{work_id}")' in content:
            print("   ✅ Work detail uses work_id (database ID) - Correct!")

def recommend_action(has_collision):
    """Provide recommendation based on analysis."""
    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    
    if has_collision:
        print("""
⚠️  ACTION REQUIRED: Psalm ID Renumbering

The database has actual ID collisions between Psalms and Works.
You need to run the renumbering script:

    python3 scripts/16_renumber_psalms.py

This will:
1. Create a backup
2. Rename all Psalm IDs: P-1 → P-3001, P-2 → P-3002, etc.
3. Verify the changes
""")
    else:
        print("""
✅ NO ACTION NEEDED (Database Structure is Correct)

However, if Windows users report seeing merged PDFs:

Possible causes:
1. Frontend bug: Check if modal/viewer uses wrong ID field
2. Search confusion: Users might see both P-1 and Work 1 in results
3. Display issue: Work numbers might be confusing to users

Recommendation for better UX:
- Keep Psalm prefix "P-" visible in all displays
- Add "(Psalm)" label in work listings
- Consider renaming anyway for clarity: P-1 → P-3001

Run renumbering script only if you want clearer distinction:
    python3 scripts/16_renumber_psalms.py
""")

def main():
    print("Emanuel Vogt Archive - Psalm ID Collision Analysis")
    print()
    
    # Step 1: Analyze structure
    analyze_id_structure()
    
    # Step 2: Check for actual collisions
    has_collision = check_viewer_collision()
    
    # Step 3: Check frontend logic
    check_frontend_logic()
    
    # Step 4: Recommend action
    recommend_action(has_collision)

if __name__ == "__main__":
    main()
