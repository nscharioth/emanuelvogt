#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Encoding Diagnostic Tool
Run this on Windows machine to diagnose encoding issues.
"""

import sqlite3
import sys
import locale
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data/archive.db"

def print_system_info():
    """Print system encoding information."""
    print("=" * 70)
    print("SYSTEM ENCODING INFORMATION")
    print("=" * 70)
    print(f"Python version: {sys.version}")
    print(f"Default encoding: {sys.getdefaultencoding()}")
    print(f"Filesystem encoding: {sys.getfilesystemencoding()}")
    print(f"Locale encoding: {locale.getpreferredencoding()}")
    print(f"stdout encoding: {sys.stdout.encoding}")
    print()

def test_database_connection():
    """Test different text_factory settings."""
    print("=" * 70)
    print("DATABASE CONNECTION TESTS")
    print("=" * 70)
    
    # Test 1: Default (str)
    print("\n[Test 1] Default text_factory (str):")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT filename FROM files WHERE filename LIKE '%ü%' OR filename LIKE '%ä%' LIMIT 1")
        result = c.fetchone()
        if result:
            print(f"  Result: {result[0]}")
            print(f"  Type: {type(result[0])}")
            print(f"  Repr: {repr(result[0])}")
        conn.close()
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # Test 2: Bytes
    print("\n[Test 2] text_factory = bytes:")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.text_factory = bytes
        c = conn.cursor()
        c.execute("SELECT filename FROM files WHERE filename LIKE '%ü%' OR filename LIKE '%ä%' LIMIT 1")
        result = c.fetchone()
        if result:
            print(f"  Result (bytes): {result[0]}")
            print(f"  UTF-8 decode: {result[0].decode('utf-8')}")
            print(f"  Windows-1252 decode: {result[0].decode('windows-1252', errors='replace')}")
        conn.close()
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # Test 3: Lambda with utf-8 errors='replace'
    print("\n[Test 3] text_factory with utf-8 errors='replace':")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.text_factory = lambda x: x.decode('utf-8', errors='replace')
        c = conn.cursor()
        c.execute("SELECT filename FROM files WHERE filename LIKE '%ü%' OR filename LIKE '%ä%' LIMIT 1")
        result = c.fetchone()
        if result:
            print(f"  Result: {result[0]}")
            print(f"  Contains replacement char �: {'�' in result[0]}")
        conn.close()
    except Exception as e:
        print(f"  ERROR: {e}")

def test_sample_files():
    """Test reading specific files with umlauts."""
    print("\n" + "=" * 70)
    print("SAMPLE FILES WITH UMLAUTS")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = bytes  # Get raw bytes
    c = conn.cursor()
    
    # Get files with umlauts
    c.execute("""
        SELECT id, filename, filepath 
        FROM files 
        WHERE filename LIKE '%ü%' OR filename LIKE '%ä%' OR filename LIKE '%ö%' OR filename LIKE '%ß%'
        LIMIT 5
    """)
    
    print("\nFiles containing umlauts (raw bytes):")
    for file_id, filename_bytes, filepath_bytes in c.fetchall():
        print(f"\nFile ID {file_id}:")
        print(f"  Filename (bytes): {filename_bytes}")
        print(f"  Filename (UTF-8): {filename_bytes.decode('utf-8', errors='replace')}")
        print(f"  Has � (replacement): {'�' in filename_bytes.decode('utf-8', errors='replace')}")
        
        # Try to find actual umlaut bytes
        if b'\xc3\xa4' in filename_bytes:
            print(f"  Contains ä (UTF-8 encoded correctly)")
        if b'\xc3\xbc' in filename_bytes:
            print(f"  Contains ü (UTF-8 encoded correctly)")
        if b'\xc3\xb6' in filename_bytes:
            print(f"  Contains ö (UTF-8 encoded correctly)")
    
    conn.close()

def test_backend_simulation():
    """Simulate backend.py connection."""
    print("\n" + "=" * 70)
    print("SIMULATING BACKEND.PY CONNECTION")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = lambda x: x.decode('utf-8', errors='replace')
    c = conn.cursor()
    
    # Simulate API query
    print("\nSimulating: GET /api/works?q=grüßen")
    c.execute("""
        SELECT id, work_number, title 
        FROM works 
        WHERE title LIKE ? 
        LIMIT 3
    """, ('%grüßen%',))
    
    results = c.fetchall()
    print(f"Found {len(results)} results:")
    for work_id, work_num, title in results:
        print(f"  {work_num}: {title}")
        print(f"    Contains �: {'�' in title}")
    
    conn.close()

def main():
    print("Windows Encoding Diagnostic Tool")
    print("Please run this script on the Windows machine and send the output.")
    print()
    
    print_system_info()
    test_database_connection()
    test_sample_files()
    test_backend_simulation()
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print("\nPlease send this entire output for analysis.")
    print("\nIf you see � (replacement characters), encoding is broken.")
    print("If you see proper umlauts (ä, ö, ü, ß), encoding is working.")

if __name__ == "__main__":
    main()
