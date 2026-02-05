#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Phase 5: Database Initialization (Robust Version V2)
Handles multi-work files, ID collisions, and complex filename parsing including ranges.
"""

import sqlite3
import pandas as pd
from pathlib import Path
import re
import sys

# Define paths
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "archive.db"
CSV_PATH = DATA_DIR / "file_inventory.csv"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS works (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_number TEXT UNIQUE NOT NULL,
        title TEXT,
        sort_title TEXT,
        composer TEXT DEFAULT 'Emanuel Vogt',
        year INTEGER,
        genre TEXT,
        instrumentation TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_id INTEGER,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        file_type TEXT,
        size_bytes INTEGER,
        page_count INTEGER,
        width INTEGER,
        height INTEGER,
        dpi INTEGER,
        is_public BOOLEAN DEFAULT 1,
        FOREIGN KEY (work_id) REFERENCES works (id)
    )
    ''')
    
    c.execute('CREATE INDEX IF NOT EXISTS idx_work_number ON works (work_number)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_title ON works (title)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_files_work_id ON files (work_id)')
    
    conn.commit()
    conn.close()
    print("✅ Database schema initialized.")

def clean_id(s):
    """Clean extra characters from a potential ID."""
    if not s: return ""
    # Remove trailing dots, dashes, spaces
    return re.sub(r'[^a-zA-Z0-9]$', '', s.strip())

def parse_work_ids(filename, raw_csv_work_num):
    """
    Robustly extract all Work IDs from a filename.
    Handles: "2015, 2016", "12a, b, c", "961 bis 963", "1691 - 1711"
    """
    ids = set()
    
    # 1. Detect Ranges first
    # Pattern: "961 bis 963" or "1691 - 1711"
    range_patterns = [
        r'(\d+)\s+bis\s+(\d+)',
        r'^(\d+)\s*-\s*(\d+)\s*-' # Specifically for "1691 - 1711 - Title"
    ]
    
    for pat in range_patterns:
        match = re.search(pat, filename, re.I)
        if match:
            start, end = map(int, match.groups())
            if 0 < (end - start) < 250: # Safety cap
                for n in range(start, end + 1):
                    ids.add(str(n))

    # 2. Hyphen split and conjunctions
    if " - " in filename:
        prefix = filename.split(" - ")[0]
        # Split prefix by common delimiters
        parts = re.split(r',| und | and | & ', prefix, flags=re.I)
        
        last_base_num = ""
        for p in parts:
            p = p.strip()
            if not p: continue
            
            # Match digits + optional letter (e.g. 12a, 2015)
            match = re.match(r'^(\d+)([a-z])?$', p, re.I)
            if match:
                num, letter = match.groups()
                ids.add(p)
                last_base_num = num
            # Match just a letter if we have a base (e.g. "b" in "12a, b")
            elif re.match(r'^[a-z]$', p, re.I) and last_base_num:
                ids.add(f"{last_base_num}{p}")
            else:
                m = re.match(r'^(\d+[a-z]?)', p, re.I)
                if m:
                    ids.add(m.group(1))

    # 3. Secondary scan for "und/and ID" anywhere
    matches = re.findall(r'(?:und|and|&)\s+(\d+[a-z]?)', filename, re.I)
    for m in matches:
        ids.add(m)

    # 4. Include CSV detected ID
    if raw_csv_work_num and pd.notna(raw_csv_work_num):
        ids.add(str(raw_csv_work_num).strip())

    # Final cleaning
    clean_ids = {clean_id(i) for i in ids if i}
    return sorted(list(clean_ids))

def guess_title_from_filename(filename, work_number):
    base = Path(filename).stem
    if " - " in base:
        title = base.split(" - ", 1)[1]
    else:
        title = base
    title = re.sub(r'\s*-\s*(Seite|Seiten|Titelseite).*$', '', title, flags=re.I)
    return title.strip()

def import_data():
    if not CSV_PATH.exists():
        print("❌ CSV not found.")
        return
        
    df = pd.read_csv(CSV_PATH)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    works_count = 0
    files_linked = 0
    
    print(f"Importing from {len(df)} rows...")
    
    for _, row in df.iterrows():
        filename = str(row['filename'])
        filepath = str(row['filepath'])
        raw_num = str(row['work_number'])
        
        extracted_ids = parse_work_ids(filename, raw_num)
        
        for eid in extracted_ids:
            if "/Psalmen/" in filepath:
                work_num = f"P-{eid}" if not eid.startswith("P-") else eid
                genre = "Psalm"
            else:
                work_num = eid
                genre = "Werk"

            # 1. Ensure Work exists
            c.execute('SELECT id FROM works WHERE work_number = ?', (work_num,))
            res = c.fetchone()
            if res:
                work_id = res[0]
            else:
                title = guess_title_from_filename(filename, eid)
                c.execute('INSERT INTO works (work_number, title, genre) VALUES (?, ?, ?)',
                          (work_num, title, genre))
                work_id = c.lastrowid
                works_count += 1
                
            # 2. Link File
            c.execute('SELECT id FROM files WHERE filepath = ? AND work_id = ?', (filepath, work_id))
            if not c.fetchone():
                c.execute('''
                INSERT INTO files (work_id, filename, filepath, file_type, size_bytes)
                VALUES (?, ?, ?, ?, ?)
                ''', (work_id, filename, filepath, row['file_type'], row['file_size_bytes']))
                files_linked += 1
                
    conn.commit()
    conn.close()
    print(f"✅ Import complete: {works_count} new works, {files_linked} file links created.")

if __name__ == "__main__":
    init_db()
    import_data()
