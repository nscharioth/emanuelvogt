#!/usr/bin/env python3
import sqlite3
import re

DB_PATH = "data/archive.db"

def audit():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all work numbers that are primarily numeric (the standard "Werke")
    c.execute("SELECT work_number FROM works WHERE work_number NOT LIKE 'P-%'")
    ids = [row[0] for row in c.fetchall()]
    
    def get_main_num(s):
        match = re.search(r'^(\d+)', s)
        return int(match.group(1)) if match else None

    numeric_ids = {get_main_num(i) for i in ids if get_main_num(i)}
    max_id = max(numeric_ids) if numeric_ids else 0
    missing = sorted(list(set(range(1, max_id + 1)) - numeric_ids))
    
    psalms_count = conn.execute("SELECT COUNT(*) FROM works WHERE work_number LIKE 'P-%'").fetchone()[0]
    total_works = conn.execute("SELECT COUNT(*) FROM works").fetchone()[0]

    report = f"""
Emanuel Vogt Archive Quality Audit
==================================
Total Works in Database: {total_works}
  - Standard Werke: {total_works - psalms_count}
  - Psalmen: {psalms_count}

Numeric Range Profile:
  - Max ID found: {max_id}
  - Distinct numeric bases found: {len(numeric_ids)}
  - Gaps in sequence (missing numbers): {len(missing)}

Completeness: {(len(numeric_ids)/max_id*100 if max_id else 0):.1f}%
    """
    
    print(report)
    
    with open("data/FINAL_AUDIT_REPORT.txt", "w") as f:
        f.write(report)
        f.write("\nMissing IDs (Numeric gaps):\n")
        for i in range(0, len(missing), 15):
            f.write(", ".join(map(str, missing[i:i+15])) + "\n")

if __name__ == "__main__":
    audit()
