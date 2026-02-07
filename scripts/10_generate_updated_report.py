#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Generate New Missing Works Report
After ID corrections in Phase 7
"""

import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "archive.db"
OUTPUT_FILE = DATA_DIR / "MISSING_WORKS_V5_UPDATED.txt"

def get_all_work_numbers(conn):
    """Get all work numbers from database."""
    c = conn.cursor()
    c.execute("SELECT work_number FROM works WHERE work_number NOT LIKE 'P-%'")
    return [int(row[0]) for row in c.fetchall() if row[0].isdigit()]

def find_missing_ranges(numbers):
    """Find missing numbers in sequence."""
    if not numbers:
        return []
    
    numbers = sorted(set(numbers))
    max_num = max(numbers)
    all_nums = set(range(1, max_num + 1))
    existing = set(numbers)
    missing = sorted(all_nums - existing)
    return missing

def main():
    print("Emanuel Vogt Archive - Updated Missing Works Analysis")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get statistics
    c.execute("SELECT COUNT(*) FROM works")
    total_works = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM works WHERE work_number LIKE 'P-%'")
    psalm_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM works WHERE work_number NOT LIKE 'P-%'")
    standard_works = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM files")
    total_files = c.fetchone()[0]
    
    # Get all work numbers
    work_numbers = get_all_work_numbers(conn)
    max_id = max(work_numbers) if work_numbers else 0
    
    # Find missing
    missing = find_missing_ranges(work_numbers)
    
    # Calculate completeness
    completeness = (len(work_numbers) / max_id * 100) if max_id > 0 else 0
    
    # Print summary
    print(f"\nTotal Works in DB: {total_works}")
    print(f"  - Standard Works: {standard_works}")
    print(f"  - Psalmen: {psalm_count}")
    print(f"Total Files: {total_files}")
    print(f"Max Work ID Found: {max_id}")
    print(f"Missing numeric IDs: {len(missing)}")
    print(f"Completeness vs ID Range: {completeness:.1f}%")
    
    # Write report
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("Emanuel Vogt Archive - Updated Data Audit (Phase 7)\n")
        f.write("=" * 70 + "\n")
        f.write(f"Date: February 7, 2026\n")
        f.write(f"Total Works in DB: {total_works} (Includes ~{psalm_count} Psalms)\n")
        f.write(f"Standard Works: {standard_works}\n")
        f.write(f"Total Files: {total_files}\n")
        f.write(f"Max Work ID Found: {max_id}\n")
        f.write(f"Missing numeric IDs: {len(missing)}\n")
        f.write(f"Completeness vs ID Range: {completeness:.1f}%\n\n")
        
        f.write("=" * 70 + "\n")
        f.write("STATUS: Phase 7 Corrections Applied\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("✅ Fixed Issues:\n")
        f.write("-" * 70 + "\n")
        f.write("• Work 381: Added (-.pdf file)\n")
        f.write("• Work 531: Corrected from misassigned 529/530\n")
        f.write("• Works 599-607: Added (Bicinien collection)\n")
        f.write("• Works 616-622: Added (Bleistift-Manuskripte)\n")
        f.write("• Work 655: Corrected from 656\n")
        f.write("• Works 691-703: Added (Notenheft fragments)\n")
        f.write("• Work 878: Added (Präludium in G-Dur)\n")
        f.write("• Work 902: Corrected from 901\n")
        f.write("• Work 913: Verified correct\n")
        f.write("• Work 915: Corrected from 914\n")
        f.write("• Works 1028-1029: Added (multi-work file)\n")
        f.write("• Work 1056: Added (Tischsonate)\n")
        f.write("• Works 1068-1070: Added (Hab mein Wagen)\n")
        f.write("• Work 1085: Added (Adventsruf continuation)\n")
        f.write("• Work 1347: Added\n")
        f.write("• Works 1550-1560: Added (Image files, excluding 1554)\n")
        f.write("• Work 1664: Corrected from 1554\n")
        f.write("• Works 1790-1791: Added\n")
        f.write("• Work 1996: Added\n")
        f.write("• Work 2002: Added\n")
        f.write("• Work 2007: Corrected from 2006\n")
        f.write("• Works 2024-2025: Added\n\n")
        
        if missing:
            f.write(f"Remaining Missing Work Numbers ({len(missing)} gaps):\n")
            f.write("-" * 70 + "\n")
            # Format missing numbers in rows of 10
            for i in range(0, len(missing), 10):
                row = missing[i:i+10]
                f.write(", ".join(map(str, row)) + "\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("NOTES ON REMAINING GAPS:\n")
            f.write("=" * 70 + "\n\n")
            f.write("The remaining gaps may be due to:\n")
            f.write("1. Works that were never assigned these numbers\n")
            f.write("2. Works that were lost or destroyed\n")
            f.write("3. Works that exist but were not included in the archive\n")
            f.write("4. Numbering system gaps (intentional skips)\n")
            f.write("5. Works that require physical verification in original archive\n\n")
            f.write("ACTION REQUIRED:\n")
            f.write("• Verify with original physical archive\n")
            f.write("• Cross-reference with Excel catalogs\n")
            f.write("• Check GEMA registration records\n")
        else:
            f.write("🎉 NO MISSING WORK NUMBERS! Archive is 100% complete!\n")
    
    print(f"\n✅ Report written to: {OUTPUT_FILE}")
    print(f"\n📊 Summary:")
    print(f"   Before Phase 7: 139 missing IDs")
    print(f"   After Phase 7:  {len(missing)} missing IDs")
    print(f"   IDs Recovered:  {139 - len(missing)}")
    print(f"   Improvement:    {(139 - len(missing)) / 139 * 100:.1f}%")
    
    conn.close()

if __name__ == "__main__":
    main()
