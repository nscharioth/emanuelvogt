#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Phase 7: Fix Missing Work IDs
Corrects misassigned IDs and adds missing works based on manual audit findings.
"""

import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "archive.db"
ARCHIVE_DIR = Path(__file__).parent.parent / "archive"

def get_file_id_by_path(conn, partial_path):
    """Find file ID by partial path match."""
    c = conn.cursor()
    query = f"%{partial_path}%"
    c.execute("SELECT id, filepath FROM files WHERE filepath LIKE ?", (query,))
    result = c.fetchone()
    return result[0] if result else None

def get_work_id_by_number(conn, work_number):
    """Get work ID by work_number."""
    c = conn.cursor()
    c.execute("SELECT id FROM works WHERE work_number = ?", (work_number,))
    result = c.fetchone()
    return result[0] if result else None

def create_work(conn, work_number, title, genre=None):
    """Create a new work entry."""
    c = conn.cursor()
    c.execute("""
        INSERT INTO works (work_number, title, sort_title, genre)
        VALUES (?, ?, ?, ?)
    """, (work_number, title, title, genre))
    conn.commit()
    return c.lastrowid

def link_file_to_work(conn, file_id, work_id):
    """Update file to link to specific work."""
    c = conn.cursor()
    c.execute("UPDATE files SET work_id = ? WHERE id = ?", (work_id, file_id))
    conn.commit()

def fix_misassigned_ids(conn):
    """Fix IDs that were incorrectly parsed from filenames."""
    print("\n🔧 Fixing misassigned IDs...")
    
    fixes = [
        # Format: (partial_path, correct_work_number, title)
        ("529 und 530 - Vorspiel", "531", "Vorspiel zu Lobe den Herren"),
        ("656 - Missa", "655", "Missa für Männerchor (Werk 655)"),
        ("877 - Präludium in G-Dur", "878", "Präludium in G-Dur"),
        ("901 - Bei Dir Jesus", "902", "Bei Dir Jesus will ich bleiben"),
        ("913 - Vater unser", "913", "Vater unser im Himmel"),
        ("914 - Nun singet", "915", "Nun singet und seid froh"),
        ("1554 - Leise rieselt", "1664", "Leise rieselt der Schnee"),
        ("2006 - Gottes Sohn", "2007", "Gottes Sohn ist kommen"),
    ]
    
    for partial_path, correct_id, title in fixes:
        file_id = get_file_id_by_path(conn, partial_path)
        if not file_id:
            print(f"  ⚠️  File not found: {partial_path}")
            continue
        
        # Check if work already exists
        work_id = get_work_id_by_number(conn, correct_id)
        if not work_id:
            work_id = create_work(conn, correct_id, title)
            print(f"  ✅ Created work {correct_id}: {title}")
        
        # Link file to correct work
        link_file_to_work(conn, file_id, work_id)
        print(f"  ✅ Fixed: {partial_path} → Work {correct_id}")

def add_multi_work_files(conn):
    """Add entries for works that are embedded in multi-work files."""
    print("\n🔧 Adding works from multi-work files...")
    
    multi_works = [
        # Format: (partial_path, [(work_num, title)])
        ("599 - 607 Sammlung", [
            ("599", "Bicinien - Werk 599"),
            ("600", "Bicinien - Werk 600"),
            ("601", "Bicinien - Werk 601"),
            ("602", "Bicinien - Werk 602"),
            ("603", "Bicinien - Werk 603"),
            ("604", "Bicinien - Werk 604"),
            ("605", "Bicinien - Werk 605"),
            ("606", "Bicinien - Werk 606"),
            ("607", "Bicinien - Werk 607"),
        ]),
        ("616 - 622 Bleistift", [
            ("617", "Bleistift-Manuskript - Werk 617"),
            ("618", "Bleistift-Manuskript - Werk 618"),
            ("619", "Bleistift-Manuskript - Werk 619"),
            ("620", "Bleistift-Manuskript - Werk 620"),
            ("621", "Bleistift-Manuskript - Werk 621"),
            ("622", "Bleistift-Manuskript - Werk 622"),
        ]),
        ("690 - 703", [
            ("691", "Aus einem Notenheft - Werk 691"),
            ("692", "Aus einem Notenheft - Werk 692"),
            ("693", "Aus einem Notenheft - Werk 693"),
            ("694", "Aus einem Notenheft - Werk 694"),
            ("695", "Aus einem Notenheft - Werk 695"),
            ("696", "Aus einem Notenheft - Werk 696"),
            ("697", "Aus einem Notenheft - Werk 697"),
            ("698", "Aus einem Notenheft - Werk 698"),
            ("699", "Aus einem Notenheft - Werk 699"),
            ("700", "Aus einem Notenheft - Werk 700"),
            ("701", "Aus einem Notenheft - Werk 701"),
            ("702", "Aus einem Notenheft - Werk 702"),
            ("703", "Aus einem Notenheft - Werk 703"),
        ]),
        ("1027 - Christus", [
            ("1028", "Wir danken dir"),
            ("1029", "Liebster Jesu, wir sind hier"),
        ]),
        ("1054 - 1055 - 1056", [
            ("1056", "Tischsonate - Satz 4"),
        ]),
        ("1067 - Hab mein Wagen", [
            ("1068", "Hab mein Wagen - Teil 2"),
            ("1069", "Hab mein Wagen - Teil 3"),
            ("1070", "Hab mein Wagen - Teil 4"),
        ]),
        ("1084 - Adventsruf", [
            ("1085", "Adventsruf (Fortsetzung)"),
        ]),
        ("1346, 1247", [
            ("1347", "Der Schöpfer aller Wesen"),
        ]),
        ("1788, 1789", [
            ("1790", "Wie soll ich dich (Fortsetzung)"),
            ("1791", "O Heiland"),
        ]),
        ("1995, 2003", [
            ("1996", "Zeuch ein - Manual"),
            ("2002", "Zeuch ein - Pedal"),
        ]),
        ("2026 - Herr gibt", [
            ("2024", "O komm"),
            ("2025", "Jahresspruch 1997"),
        ]),
    ]
    
    for partial_path, works_list in multi_works:
        file_id = get_file_id_by_path(conn, partial_path)
        if not file_id:
            print(f"  ⚠️  File not found: {partial_path}")
            continue
        
        for work_num, title in works_list:
            work_id = get_work_id_by_number(conn, work_num)
            if not work_id:
                work_id = create_work(conn, work_num, title, "Fragment/Multi-Work")
                print(f"  ✅ Created work {work_num}: {title}")
                # Link to parent file
                link_file_to_work(conn, file_id, work_id)

def add_image_files(conn):
    """Add works from Image_XXX.pdf files (1550-1560)."""
    print("\n🔧 Adding works from Image files...")
    
    image_mappings = [
        ("Image_001.pdf", "1550", "Werk 1550"),
        ("Image_002.pdf", "1551", "Werk 1551"),
        ("Image_003.pdf", "1552", "Werk 1552"),
        ("Image_004.pdf", "1553", "Werk 1553"),
        ("Image_006.pdf", "1555", "Werk 1555"),
        ("Image_007.pdf", "1556", "Werk 1556"),
        ("Image_008.pdf", "1557", "Werk 1557"),
        ("Image_009.pdf", "1558", "Werk 1558"),
        ("Image_010.pdf", "1559", "Werk 1559"),
        ("Image_011.pdf", "1560", "Werk 1560"),
    ]
    
    for filename, work_num, title in image_mappings:
        file_id = get_file_id_by_path(conn, filename)
        if not file_id:
            print(f"  ⚠️  File not found: {filename}")
            continue
        
        work_id = get_work_id_by_number(conn, work_num)
        if not work_id:
            work_id = create_work(conn, work_num, title)
            print(f"  ✅ Created work {work_num}: {title}")
        
        link_file_to_work(conn, file_id, work_id)
        print(f"  ✅ Linked {filename} → Work {work_num}")

def add_special_case_381(conn):
    """Handle the special case of work 381 with -.pdf filename."""
    print("\n🔧 Adding special case: Work 381...")
    
    file_id = get_file_id_by_path(conn, "Werke 381 bis 400/-.pdf")
    if not file_id:
        print("  ⚠️  File '-.pdf' not found")
        return
    
    work_id = get_work_id_by_number(conn, "381")
    if not work_id:
        work_id = create_work(conn, "381", "Werk 381 (ohne Titel)")
        print(f"  ✅ Created work 381: Werk 381 (ohne Titel)")
    
    link_file_to_work(conn, file_id, work_id)
    print(f"  ✅ Linked -.pdf → Work 381")

def main():
    print("Emanuel Vogt Archive - Fixing Missing Work IDs")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Execute all fixes
        fix_misassigned_ids(conn)
        add_multi_work_files(conn)
        add_image_files(conn)
        add_special_case_381(conn)
        
        # Get final counts
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM works")
        total_works = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM files")
        total_files = c.fetchone()[0]
        
        print("\n" + "=" * 60)
        print(f"✅ Database update complete!")
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
