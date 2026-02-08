#!/usr/bin/env python3
"""
Script 26: Interactive Assignment of Orphaned Files
Helps manually assign orphaned files to works in the database.
"""

import sqlite3
import os
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional

# Configuration
DB_PATH = "data/archive.db"
FLAT_DIR = "archive/flat"


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    if not text:
        return ""
    
    # First normalize to NFC (composed form)
    text = unicodedata.normalize('NFC', text)
    
    # Replace German umlauts and special characters
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
        'ß': 'ss', 'ẞ': 'SS'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Convert to lowercase
    text = text.lower()
    
    # Normalize to NFKD after umlaut replacement
    text = unicodedata.normalize('NFKD', text)
    
    # Remove combining characters
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    return text


def get_orphaned_files() -> List[str]:
    """Get list of orphaned files (not in database)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all registered files
    cursor.execute("SELECT flat_path FROM files WHERE flat_path IS NOT NULL")
    registered = {row[0] for row in cursor.fetchall()}
    conn.close()
    
    # Get all files in flat directory
    flat_dir = Path(FLAT_DIR)
    all_files = [f.name for f in flat_dir.iterdir() if f.is_file()]
    
    # Find orphaned files
    orphaned = [f for f in all_files if f not in registered]
    
    return sorted(orphaned)


def search_works(query: str) -> List[Dict]:
    """Search for works by work_number or title."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    search_pattern = f"%{query}%"
    cursor.execute("""
        SELECT id, work_number, title, year, instrumentation
        FROM works
        WHERE work_number LIKE ? OR title LIKE ?
        ORDER BY work_number
        LIMIT 20
    """, (search_pattern, search_pattern))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


def get_work_by_id(work_id: int) -> Optional[Dict]:
    """Get work details by ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, work_number, title, year, instrumentation
        FROM works
        WHERE id = ?
    """, (work_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def build_new_filename(work_number: str, title: str, extension: str, file_id: int) -> str:
    """Build consistent filename."""
    work_slug = slugify(work_number) if work_number else f"work-{file_id}"
    title_slug = slugify(title)[:60] if title else "untitled"
    
    filename = f"{work_slug}-{title_slug}-{file_id}.{extension}"
    return filename


def assign_file_to_work(filename: str, work_id: int, description: str = None) -> bool:
    """
    Assign orphaned file to a work.
    Creates database entry and renames file.
    """
    flat_path = Path(FLAT_DIR) / filename
    
    if not flat_path.exists():
        print(f"❌ Error: File {filename} not found!")
        return False
    
    # Get work details
    work = get_work_by_id(work_id)
    if not work:
        print(f"❌ Error: Work ID {work_id} not found!")
        return False
    
    # Extract extension
    extension = filename.split('.')[-1] if '.' in filename else 'pdf'
    
    # Determine original path (use current filename as placeholder)
    original_path = f"orphaned/{filename}"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Insert file record
        cursor.execute("""
            INSERT INTO files (work_id, filepath, file_type, description)
            VALUES (?, ?, ?, ?)
        """, (work_id, original_path, extension.upper(), description))
        
        file_id = cursor.lastrowid
        
        # Build new filename
        new_filename = build_new_filename(
            work['work_number'],
            work['title'],
            extension,
            file_id
        )
        
        new_path = Path(FLAT_DIR) / new_filename
        
        # Check if new filename already exists
        if new_path.exists():
            print(f"⚠️  Warning: {new_filename} already exists!")
            new_filename = f"{work['work_number']}-{slugify(work['title'])[:40]}-{file_id}-alt.{extension}"
            new_path = Path(FLAT_DIR) / new_filename
        
        # Rename file
        os.rename(flat_path, new_path)
        
        # Update database with new flat_path
        cursor.execute("""
            UPDATE files SET flat_path = ? WHERE id = ?
        """, (new_filename, file_id))
        
        conn.commit()
        
        print(f"\n✅ Success!")
        print(f"   File ID: {file_id}")
        print(f"   Work: {work['work_number']} - {work['title']}")
        print(f"   Old: {filename}")
        print(f"   New: {new_filename}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()


def preview_file(filename: str):
    """Show file info and open in system viewer."""
    filepath = Path(FLAT_DIR) / filename
    
    if not filepath.exists():
        print(f"❌ File not found: {filename}")
        return
    
    size_mb = filepath.stat().st_size / (1024 * 1024)
    print(f"\n📄 File: {filename}")
    print(f"   Size: {size_mb:.1f} MB")
    print(f"   Path: {filepath}")
    
    # Try to open file
    try:
        import subprocess
        subprocess.run(['open', str(filepath)], check=False)
        print("   ✓ Opened in system viewer")
    except Exception as e:
        print(f"   ⚠️  Could not open: {e}")


def interactive_assignment():
    """Interactive assignment loop."""
    print("="*80)
    print("Interactive File Assignment")
    print("="*80)
    
    # Get orphaned files
    orphaned = get_orphaned_files()
    
    if not orphaned:
        print("\n✅ No orphaned files found! All files are assigned.")
        return
    
    print(f"\nFound {len(orphaned)} orphaned files:")
    for i, f in enumerate(orphaned[:10], 1):
        print(f"  {i:2d}. {f}")
    if len(orphaned) > 10:
        print(f"  ... and {len(orphaned) - 10} more")
    
    print("\n" + "="*80)
    
    # Process each file
    for i, filename in enumerate(orphaned, 1):
        print(f"\n\n{'='*80}")
        print(f"File {i}/{len(orphaned)}: {filename}")
        print("="*80)
        
        while True:
            print("\nOptions:")
            print("  [p] Preview file (open in system viewer)")
            print("  [s] Search for work")
            print("  [a] Assign to work by ID")
            print("  [k] Skip this file")
            print("  [q] Quit")
            
            choice = input("\nYour choice: ").strip().lower()
            
            if choice == 'p':
                preview_file(filename)
                
            elif choice == 's':
                query = input("Search query (work number or title): ").strip()
                if query:
                    results = search_works(query)
                    if results:
                        print(f"\nFound {len(results)} works:")
                        for work in results:
                            instrumentation = work['instrumentation'] or ''
                            year = work['year'] or ''
                            print(f"  [{work['id']:4d}] {work['work_number']:6s} | {work['title'][:50]:50s} | {year} {instrumentation[:20]}")
                    else:
                        print("No works found.")
                        
            elif choice == 'a':
                try:
                    work_id = int(input("Work ID: ").strip())
                    description = input("Description (optional): ").strip() or None
                    
                    # Show work details
                    work = get_work_by_id(work_id)
                    if work:
                        print(f"\nAssigning to:")
                        print(f"  Work {work['work_number']}: {work['title']}")
                        confirm = input("Confirm? [y/N]: ").strip().lower()
                        
                        if confirm == 'y':
                            if assign_file_to_work(filename, work_id, description):
                                break  # Move to next file
                    else:
                        print(f"Work ID {work_id} not found.")
                        
                except ValueError:
                    print("Invalid work ID.")
                    
            elif choice == 'k':
                print("⏭  Skipping file...")
                break
                
            elif choice == 'q':
                print("\n👋 Quitting...")
                return
                
            else:
                print("Invalid choice.")
    
    print("\n" + "="*80)
    print("✅ All files processed!")
    print("="*80)


def main():
    """Main execution"""
    if not Path(DB_PATH).exists():
        print(f"❌ Error: Database not found at {DB_PATH}")
        return
    
    if not Path(FLAT_DIR).exists():
        print(f"❌ Error: Directory not found: {FLAT_DIR}")
        return
    
    interactive_assignment()


if __name__ == "__main__":
    main()
