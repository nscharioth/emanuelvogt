#!/usr/bin/env python3
"""
Script 25: Identify Orphaned Files in archive/flat/
Lists files in archive/flat/ that are not registered in the database.
These files need manual work association before they can be used.
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Set

# Configuration
DB_PATH = "data/archive.db"
FLAT_DIR = "archive/flat"


def get_registered_filenames() -> Set[str]:
    """
    Get all filenames that are registered in the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT flat_path FROM files WHERE flat_path IS NOT NULL")
    registered = {row[0] for row in cursor.fetchall()}
    
    conn.close()
    
    return registered


def get_filesystem_files() -> List[str]:
    """
    Get all files in the flat directory.
    """
    flat_dir = Path(FLAT_DIR)
    
    if not flat_dir.exists():
        print(f"❌ Error: {FLAT_DIR} does not exist!")
        return []
    
    files = []
    for item in flat_dir.iterdir():
        if item.is_file():
            files.append(item.name)
    
    return sorted(files)


def analyze_orphaned_files():
    """
    Identify and report on orphaned files.
    """
    print("🔍 Analyzing archive/flat/ directory...\n")
    
    # Get registered files from database
    print("📊 Loading database entries...")
    registered_files = get_registered_filenames()
    print(f"   Found {len(registered_files)} files in database")
    
    # Get files from filesystem
    print("📁 Scanning filesystem...")
    filesystem_files = get_filesystem_files()
    print(f"   Found {len(filesystem_files)} files on disk\n")
    
    # Find orphaned files (in filesystem but not in database)
    orphaned = []
    for filename in filesystem_files:
        if filename not in registered_files:
            orphaned.append(filename)
    
    if not orphaned:
        print("✅ All files in archive/flat/ are properly registered in the database!")
        return
    
    # Report orphaned files
    print(f"{'='*80}")
    print(f"⚠️  Found {len(orphaned)} ORPHANED FILES (not in database)")
    print(f"{'='*80}\n")
    
    # Group by prefix pattern
    prefixes = {}
    for filename in orphaned:
        if filename.startswith('file-'):
            prefix = 'file-'
        elif filename.startswith('image-'):
            prefix = 'image-'
        elif filename.startswith('scan-'):
            prefix = 'scan-'
        else:
            prefix = 'other'
        
        if prefix not in prefixes:
            prefixes[prefix] = []
        prefixes[prefix].append(filename)
    
    # Show grouped results
    for prefix, files in sorted(prefixes.items()):
        print(f"\n📋 Files starting with '{prefix}': {len(files)}")
        print("-" * 80)
        
        for i, filename in enumerate(files, 1):
            filepath = Path(FLAT_DIR) / filename
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"  {i:2d}. {filename:60s} ({size_mb:.1f} MB)")
        
        if len(files) > 20:
            print(f"  ... showing first 20 of {len(files)} files")
            break
    
    print(f"\n{'='*80}")
    print("💡 Next Steps:")
    print("   1. Review the list of orphaned files above")
    print("   2. Determine which works these files belong to")
    print("   3. Add database entries manually or with a new import script")
    print(f"{'='*80}\n")
    
    # Save list to file
    output_file = "data/orphaned_files_report.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Orphaned Files Report - {len(orphaned)} files\n")
        f.write("=" * 80 + "\n\n")
        
        for prefix, files in sorted(prefixes.items()):
            f.write(f"\nFiles starting with '{prefix}': {len(files)}\n")
            f.write("-" * 80 + "\n")
            for filename in files:
                filepath = Path(FLAT_DIR) / filename
                size_mb = filepath.stat().st_size / (1024 * 1024)
                f.write(f"  {filename:60s} ({size_mb:.1f} MB)\n")
    
    print(f"📄 Full report saved to: {output_file}")


def main():
    """Main execution"""
    analyze_orphaned_files()


if __name__ == "__main__":
    main()
