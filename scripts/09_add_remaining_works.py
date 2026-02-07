#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Add remaining works manually
"""

import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "archive.db"
ARCHIVE_DIR = Path(__file__).parent.parent / "archive"

def create_work_if_not_exists(conn, work_number, title, genre=None):
    """Create a work if it doesn't exist."""
    c = conn.cursor()
    c.execute("SELECT id FROM works WHERE work_number = ?", (work_number,))
    if c.fetchone():
        print(f"  ⏭️  Work {work_number} already exists")
        return None
    
    c.execute("""
        INSERT INTO works (work_number, title, sort_title, genre)
        VALUES (?, ?, ?, ?)
    """, (work_number, title, title, genre))
    conn.commit()
    print(f"  ✅ Created work {work_number}: {title}")
    return c.lastrowid

def add_file_for_work(conn, work_id, filepath):
    """Add a file entry for a work."""
    if not work_id:
        return
    
    c = conn.cursor()
    filename = Path(filepath).name
    file_path = Path(ARCHIVE_DIR) / filepath
    
    if not file_path.exists():
        print(f"    ⚠️  File not found on disk: {filepath}")
        return
    
    file_size = file_path.stat().st_size
    file_type = file_path.suffix[1:].upper() if file_path.suffix else "UNKNOWN"
    
    c.execute("""
        INSERT INTO files (work_id, filename, filepath, file_type, size_bytes)
        VALUES (?, ?, ?, ?, ?)
    """, (work_id, filename, filepath, file_type, file_size))
    conn.commit()
    print(f"    ✅ Added file: {filename}")

def main():
    print("Emanuel Vogt Archive - Adding Remaining Works")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Add Bicinien works (599-607)
        print("\n🔧 Adding Bicinien works (599-607)...")
        bicinien_file = "files/Werke - außer Psalmen/Werke 581 bis 600/599 - Notenheft Bicinien/599 - 607 Sammlung aus dem Notenheft Bicinien.pdf"
        for i in range(599, 608):
            work_id = create_work_if_not_exists(conn, str(i), f"Bicinien - Werk {i}", "Bicinien")
            if work_id:
                add_file_for_work(conn, work_id, bicinien_file)
        
        # Add work 616 (was missing from earlier script)
        print("\n🔧 Adding work 616...")
        work_id = create_work_if_not_exists(conn, "616", "Bleistift-Manuskript - Werk 616", "Fragment/Multi-Work")
        
        # Add work 878 (Präludium)
        print("\n🔧 Adding work 878...")
        praludium_file = "files/Werke - außer Psalmen/Werke 861 bis 880/877 - Präludium in G-Dur.pdf"
        work_id = create_work_if_not_exists(conn, "878", "Präludium in G-Dur", "Orgel")
        if work_id:
            add_file_for_work(conn, work_id, praludium_file)
        
        # Get final counts
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM works")
        total_works = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM files")
        total_files = c.fetchone()[0]
        
        print("\n" + "=" * 60)
        print(f"✅ Update complete!")
        print(f"   Total Works: {total_works}")
        print(f"   Total Files: {total_files}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
