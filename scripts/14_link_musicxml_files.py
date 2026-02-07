#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add MusicXML files to the database.
"""

import sqlite3
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "archive.db"
MUSICXML_DIR = DATA_DIR / "manual"

def add_musicxml_column():
    """Add has_musicxml column to works table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if column exists
    c.execute("PRAGMA table_info(works)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'has_musicxml' not in columns:
        print("[*] Adding has_musicxml column to works table...")
        c.execute("ALTER TABLE works ADD COLUMN has_musicxml INTEGER DEFAULT 0")
        conn.commit()
        print("[+] Column added")
    else:
        print("[*] has_musicxml column already exists")
    
    conn.close()

def link_musicxml_files():
    """Link MusicXML files to works."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if not MUSICXML_DIR.exists():
        print(f"[-] MusicXML directory not found: {MUSICXML_DIR}")
        conn.close()
        return
    
    musicxml_files = list(MUSICXML_DIR.glob("*.musicxml"))
    print(f"[*] Found {len(musicxml_files)} MusicXML files")
    
    linked = 0
    not_found = []
    
    for file_path in musicxml_files:
        filename = file_path.name
        # Extract work number (e.g., "9 - Title.musicxml" -> "9")
        match = re.match(r'^([^-]+)\s*-', filename)
        if not match:
            print(f"[!] Could not extract work number from: {filename}")
            continue
        
        work_number = match.group(1).strip()
        
        # Find work in database
        c.execute("SELECT id, title FROM works WHERE work_number = ?", (work_number,))
        result = c.fetchone()
        
        if result:
            work_id = result[0]
            work_title = result[1]
            
            c.execute("UPDATE works SET has_musicxml = 1 WHERE id = ?", (work_id,))
            linked += 1
            print(f"[+] Linked {filename} to Work {work_number}: {work_title}")
        else:
            not_found.append((work_number, filename))
            print(f"[-] Work {work_number} not found for {filename}")
    
    conn.commit()
    conn.close()
    
    print(f"\n[*] Summary:")
    print(f"   Linked: {linked}")
    print(f"   Not found: {len(not_found)}")
    
    if not_found:
        print(f"\n[!] Works not found in database:")
        for work_num, fname in not_found:
            print(f"   - Work {work_num}: {fname}")

def main():
    print("=" * 70)
    print("Emanuel Vogt Archive - Link MusicXML Files")
    print("=" * 70)
    print()
    
    try:
        add_musicxml_column()
        link_musicxml_files()
        
        print("\n" + "=" * 70)
        print("[+] OPERATION COMPLETE")
        print("=" * 70)
    except Exception as e:
        print(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
