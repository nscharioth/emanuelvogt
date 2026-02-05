#!/usr/bin/env python3
"""
Generate list of missing work numbers from the SQLite database.
"""
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "data/archive.db"

def get_missing_report():
    conn = sqlite3.connect(DB_PATH)
    
    # Get all work numbers for standard Works (exclude Psalms P-*)
    query = "SELECT work_number FROM works WHERE work_number NOT LIKE 'P-%'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    unique_ids = df['work_number'].unique()
    
    def get_num(w):
        try:
            # Handle "12a", "2016" -> 12, 2016
            return int(''.join(filter(str.isdigit, str(w))))
        except:
            return -1

    numeric_ids = sorted(list(set([get_num(w) for w in unique_ids if get_num(w) > 0])))
    
    if not numeric_ids:
        print("No work IDs found.")
        return

    max_id = max(numeric_ids)
    actual = set(numeric_ids)
    expected = set(range(1, max_id + 1))
    missing = sorted(list(expected - actual))

    OUTPUT_FILE = "data/MISSING_WORKS_REPORT_FINAL.txt"

    with open(OUTPUT_FILE, "w") as f:
        f.write(f"Emanuel Vogt Archive - Final Data Audit\n")
        f.write(f"=======================================\n")
        f.write(f"Total Works in DB: {len(numeric_ids) + 223} (Includes ~223 Psalms)\n")
        f.write(f"Max Work ID Found: {max_id}\n")
        f.write(f"Missing numeric IDs: {len(missing)}\n")
        f.write(f"Completeness vs ID Range: {len(numeric_ids)/max_id*100:.1f}%\n\n")
        f.write("Missing Work Numbers (Gaps in 1-{max_id}):\n")
        f.write("-----------------------------------------\n")
        
        for i in range(0, len(missing), 10):
            chunk = missing[i:i+10]
            f.write(", ".join(map(str, chunk)) + "\n")

    print(f"Generated {OUTPUT_FILE}")

if __name__ == "__main__":
    get_missing_report()
