#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emanuel Vogt Archive - Phase 11: Archive Reorganization
Creates a flat, URL-safe archive structure with normalized filenames.

Strategy:
- Copy files from archive/files/ to archive/flat/
- Generate URL-safe slugs (no umlauts, special chars)
- Update database with new paths (backward compatible)
- Preserve original paths as backup

Usage:
  Dry-run (preview):        python scripts/23_reorganize_archive.py
  Test 10 files:           python scripts/23_reorganize_archive.py --live --limit=10
  Full migration:          python scripts/23_reorganize_archive.py --live
  Skip database backup:    python scripts/23_reorganize_archive.py --live --no-backup
"""

import sqlite3
import shutil
from pathlib import Path
import re
import unicodedata
from collections import defaultdict
import json
import sys
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "archive"
OLD_ARCHIVE = ARCHIVE_DIR / "files"
NEW_ARCHIVE = ARCHIVE_DIR / "flat"
DB_PATH = BASE_DIR / "data" / "archive.db"
REPORT_PATH = BASE_DIR / "data" / "reorganization_report.json"

# Configuration
DRY_RUN = True  # Set to False to actually copy files
MAX_SLUG_LENGTH = 100
BACKUP_DB = True


def slugify(text, max_length=MAX_SLUG_LENGTH):
    """
    Convert text to URL-safe slug.
    
    Rules:
    - ä → ae, ö → oe, ü → ue, ß → ss
    - Remove special characters
    - Replace spaces with hyphens
    - Lowercase
    - Collapse multiple hyphens
    - Trim to max_length
    
    Examples:
        >>> slugify("Hör, hör, hör....")
        'hoer-hoer-hoer'
        >>> slugify("Gänseblümchen")
        'gaensebluemchen'
        >>> slugify("Improperion")
        'improperion'
    """
    if not text:
        return ""
    
    # CRITICAL: Database filenames are in NFD form (decomposed: ö = o + combining-diaeresis)
    # So we MUST normalize to NFC FIRST to get composed characters (ö as single char)
    # THEN do umlaut replacements, THEN normalize remaining characters
    text = unicodedata.normalize('NFC', text)
    
    # Now do umlaut replacements (works because characters are composed)
    replacements = {
        'ä': 'ae', 'Ä': 'Ae',
        'ö': 'oe', 'Ö': 'Oe', 
        'ü': 'ue', 'Ü': 'Ue',
        'ß': 'ss',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Now normalize Unicode (for any remaining combined characters)
    text = unicodedata.normalize('NFKD', text)
    
    # Remove any remaining accents/diacritics
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    
    # Remove special characters (keep only alphanumeric and hyphens)
    text = re.sub(r'[^a-z0-9\-]', '', text)
    
    # Collapse multiple hyphens
    text = re.sub(r'-+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text


def generate_work_slug(work_number, title):
    """
    Generate slug for a work.
    Format: [ID-prefix]-[title-slug]
    
    Examples:
        >>> generate_work_slug("14a", "Hör, hör, hör....")
        '0014a-hoer-hoer-hoer'
        >>> generate_work_slug("528", "Improperion")
        '0528-improperion'
        >>> generate_work_slug("P-19", "Psalm 19")
        'p-019-psalm-19'
    """
    # Parse work number
    if work_number and work_number.startswith('P-'):
        # Psalm: "P-19" → "p-019"
        try:
            num = int(work_number.split('-')[1])
            prefix = f"p-{num:03d}"
        except (ValueError, IndexError):
            prefix = slugify(work_number)
    elif work_number:
        # Regular work: "14a" → "0014a", "528" → "0528"
        # Extract number and optional letter
        match = re.match(r'^(\d+)([a-z]*)$', work_number, re.IGNORECASE)
        if match:
            num, letter = match.groups()
            prefix = f"{int(num):04d}{letter.lower()}"
        else:
            # Complex work number (e.g., "12a, b, c")
            prefix = slugify(work_number)
    else:
        prefix = "unknown"
    
    # Generate title slug
    title_slug = slugify(title) if title else ""
    
    # Combine (limit total length)
    if title_slug:
        full_slug = f"{prefix}-{title_slug}"
    else:
        full_slug = prefix
    
    # Ensure total length is within limit
    if len(full_slug) > MAX_SLUG_LENGTH:
        available = MAX_SLUG_LENGTH - len(prefix) - 1
        if available > 0:
            title_slug = title_slug[:available]
            full_slug = f"{prefix}-{title_slug}".rstrip('-')
        else:
            full_slug = prefix[:MAX_SLUG_LENGTH]
    
    return full_slug


def generate_file_slug(filename, file_id, existing_slugs):
    """
    Generate unique slug for a file.
    Handles duplicates by appending file_id.
    
    Args:
        filename: Original filename
        file_id: Database ID for uniqueness
        existing_slugs: Set of already used slugs (without extension)
    
    Returns:
        Unique slug with extension
    """
    # Extract name and extension
    path = Path(filename)
    name = path.stem
    ext = path.suffix.lower()
    
    # Generate base slug from filename
    base_slug = slugify(name)

    
    # If slug is empty (very rare), use file_id
    if not base_slug:
        base_slug = f"file-{file_id}"
    
    # Check for duplicates
    slug = base_slug
    if slug in existing_slugs:
        # Append file_id to make unique
        slug = f"{base_slug}-{file_id}"
    
    return f"{slug}{ext}"


def backup_database():
    """Create backup of database before modifications."""
    if not BACKUP_DB:
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = DB_PATH.parent / f"archive_backup_{timestamp}.db"
    
    if not DRY_RUN:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
    else:
        print(f"[DRY RUN] Would backup database to: {backup_path}")
    
    return backup_path


def add_database_columns():
    """Add new columns to files table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if columns already exist
    c.execute("PRAGMA table_info(files)")
    columns = [row[1] for row in c.fetchall()]
    
    new_columns = []
    if 'slug' not in columns:
        new_columns.append("ALTER TABLE files ADD COLUMN slug TEXT")
    if 'flat_path' not in columns:
        new_columns.append("ALTER TABLE files ADD COLUMN flat_path TEXT")
    if 'original_path' not in columns:
        new_columns.append("ALTER TABLE files ADD COLUMN original_path TEXT")
    
    if new_columns:
        for sql in new_columns:
            if not DRY_RUN:
                c.execute(sql)
                print(f"✅ Executed: {sql}")
            else:
                print(f"[DRY RUN] Would execute: {sql}")
        
        if not DRY_RUN:
            conn.commit()
            print(f"✅ Added {len(new_columns)} new column(s)")
    else:
        print("ℹ️  Database columns already exist")
    
    conn.close()


def analyze_files():
    """
    Analyze all files and generate slugs.
    Returns dict with file info and slug mappings.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get all files with work info
    c.execute("""
        SELECT 
            f.id, f.filename, f.filepath, f.file_type,
            w.work_number, w.title
        FROM files f
        LEFT JOIN works w ON f.work_id = w.id
        ORDER BY f.id
    """)
    
    files = []
    slug_counts = defaultdict(int)
    existing_slugs = set()
    
    for row in c.fetchall():
        file_id = row['id']
        filename = row['filename']
        filepath = row['filepath']
        work_number = row['work_number']
        title = row['title']
        
        # Generate slug
        slug = generate_file_slug(filename, file_id, existing_slugs)
        existing_slugs.add(slug.rsplit('.', 1)[0])  # Add without extension
        
        # Generate flat path
        flat_path = f"flat/{slug}"
        
        # Track slug usage
        slug_counts[slug] += 1
        
        # Check if source file exists
        # IMPORTANT: filepath in DB includes "files/" prefix, but OLD_ARCHIVE already points to archive/files/
        # So we need to strip the "files/" prefix from the DB path
        relative_path = filepath
        if relative_path.startswith('files/'):
            relative_path = relative_path[6:]  # Remove "files/" prefix
        source_path = OLD_ARCHIVE / relative_path
        
        files.append({
            'id': file_id,
            'filename': filename,
            'original_path': filepath,
            'slug': slug,
            'flat_path': flat_path,
            'work_number': work_number or 'N/A',
            'title': title or 'Untitled',
            'exists': source_path.exists(),
            'source_full_path': str(source_path)
        })
    
    conn.close()
    
    return files, slug_counts


def create_flat_directory():
    """Create flat archive directory."""
    if not DRY_RUN:
        NEW_ARCHIVE.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {NEW_ARCHIVE}")
    else:
        print(f"[DRY RUN] Would create directory: {NEW_ARCHIVE}")


def copy_files(files_info, limit=None):
    """
    Copy files to flat archive.
    
    Args:
        files_info: List of file info dicts
        limit: Optional limit for testing (e.g., 10 files)
    
    Returns:
        Statistics dict
    """
    stats = {
        'copied': 0,
        'skipped': 0,
        'missing': 0,
        'errors': []
    }
    
    files_to_process = files_info[:limit] if limit else files_info
    total = len(files_to_process)
    
    print(f"\n{'='*70}")
    print(f"COPYING FILES: {total} files")
    print(f"{'='*70}\n")
    
    for i, file_info in enumerate(files_to_process, 1):
        # IMPORTANT: original_path from DB includes "files/" prefix, but OLD_ARCHIVE already points to archive/files/
        # So we need to strip the "files/" prefix from the DB path
        relative_path = file_info['original_path']
        if relative_path.startswith('files/'):
            relative_path = relative_path[6:]  # Remove "files/" prefix
        source = OLD_ARCHIVE / relative_path
        dest = NEW_ARCHIVE / file_info['slug']
        
        # Progress indicator every 100 files or at end
        if i % 100 == 0 or i == total:
            print(f"Progress: {i}/{total} ({i/total*100:.1f}%)")
        
        if not source.exists():
            stats['missing'] += 1
            stats['errors'].append({
                'file_id': file_info['id'],
                'error': 'Source file not found',
                'path': str(source)
            })
            continue
        
        if dest.exists() and not DRY_RUN:
            stats['skipped'] += 1
            continue
        
        try:
            if not DRY_RUN:
                shutil.copy2(source, dest)
                stats['copied'] += 1
            else:
                stats['copied'] += 1  # Count as "would copy" in dry-run
        except Exception as e:
            stats['errors'].append({
                'file_id': file_info['id'],
                'error': str(e),
                'source': str(source),
                'dest': str(dest)
            })
    
    return stats


def update_database(files_info):
    """Update database with new paths and slugs."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print(f"\n{'='*70}")
    print(f"UPDATING DATABASE: {len(files_info)} files")
    print(f"{'='*70}\n")
    
    updated = 0
    for file_info in files_info:
        if not DRY_RUN:
            c.execute("""
                UPDATE files
                SET slug = ?,
                    flat_path = ?,
                    original_path = COALESCE(original_path, filepath)
                WHERE id = ?
            """, (file_info['slug'], file_info['flat_path'], file_info['id']))
            updated += 1
    
    if not DRY_RUN:
        conn.commit()
        print(f"✅ Database updated: {updated} files")
    else:
        print(f"[DRY RUN] Would update {len(files_info)} database entries")
    
    conn.close()


def generate_report(files_info, slug_counts, stats):
    """Generate reorganization report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'dry_run': DRY_RUN,
        'summary': {
            'total_files': len(files_info),
            'files_copied': stats['copied'],
            'files_skipped': stats['skipped'],
            'files_missing': stats['missing'],
            'errors': len(stats['errors'])
        },
        'slug_statistics': {
            'unique_slugs': len(slug_counts),
            'duplicate_slugs': sum(1 for count in slug_counts.values() if count > 1),
            'max_slug_length': max(len(slug) for slug in slug_counts.keys()) if slug_counts else 0
        },
        'sample_slugs': [
            {
                'id': f['id'],
                'original': f['filename'],
                'slug': f['slug'],
                'work': f['work_number']
            }
            for f in files_info[:20]
        ],
        'errors': stats['errors'][:50]  # First 50 errors
    }
    
    if not DRY_RUN:
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Report saved to: {REPORT_PATH}")
    
    return report


def print_summary(report):
    """Print summary of reorganization."""
    print(f"\n{'='*70}")
    print("REORGANIZATION SUMMARY")
    print(f"{'='*70}\n")
    
    summary = report['summary']
    print(f"Mode: {'🔴 LIVE' if not DRY_RUN else '🟢 DRY RUN'}")
    print(f"Total files: {summary['total_files']}")
    print(f"{'Would copy' if DRY_RUN else 'Copied'}: {summary['files_copied']}")
    print(f"Skipped (already exist): {summary['files_skipped']}")
    print(f"Missing (source not found): {summary['files_missing']}")
    print(f"Errors: {summary['errors']}")
    
    slug_stats = report['slug_statistics']
    print(f"\nSlug Statistics:")
    print(f"  Unique slugs: {slug_stats['unique_slugs']}")
    print(f"  Duplicate slugs handled: {slug_stats['duplicate_slugs']}")
    print(f"  Max slug length: {slug_stats['max_slug_length']}")
    
    print(f"\nSample Slugs (first 20):")
    for sample in report['sample_slugs']:
        work = sample['work'][:10].ljust(10)
        orig = sample['original'][:45].ljust(45)
        print(f"  {work} | {orig} → {sample['slug']}")
    
    if report['summary']['errors'] > 0:
        print(f"\n⚠️  {report['summary']['errors']} errors occurred.")
        print(f"First 5 errors:")
        for error in report['errors'][:5]:
            print(f"  - File {error.get('file_id', 'N/A')}: {error.get('error', 'Unknown error')}")


def main():
    global DRY_RUN, BACKUP_DB
    
    # Parse command line arguments
    if '--live' in sys.argv:
        DRY_RUN = False
        print("⚠️  LIVE MODE - Files will be copied and database will be modified!")
        print("Press Ctrl+C within 3 seconds to cancel...")
        import time
        time.sleep(3)
    
    if '--no-backup' in sys.argv:
        BACKUP_DB = False
    
    # Get limit from args
    limit = None
    for arg in sys.argv:
        if arg.startswith('--limit='):
            limit = int(arg.split('=')[1])
    
    print(f"\n{'='*70}")
    print("EMANUEL VOGT ARCHIVE - REORGANIZATION SCRIPT")
    print(f"{'='*70}\n")
    print(f"Mode: {'🔴 LIVE' if not DRY_RUN else '🟢 DRY RUN'}")
    print(f"Old archive: {OLD_ARCHIVE}")
    print(f"New archive: {NEW_ARCHIVE}")
    print(f"Database: {DB_PATH}")
    if limit:
        print(f"Limit: {limit} files (testing mode)")
    print()
    
    # Step 1: Backup database
    backup_path = None
    if not DRY_RUN and BACKUP_DB:
        backup_path = backup_database()
    
    # Step 2: Add database columns
    print(f"\n{'='*70}")
    print("STEP 1: DATABASE SCHEMA UPDATE")
    print(f"{'='*70}\n")
    add_database_columns()
    
    # Step 3: Analyze files and generate slugs
    print(f"\n{'='*70}")
    print("STEP 2: ANALYZING FILES")
    print(f"{'='*70}\n")
    files_info, slug_counts = analyze_files()
    print(f"✅ Analyzed {len(files_info)} files")
    print(f"   Files with existing source: {sum(1 for f in files_info if f['exists'])}")
    print(f"   Files with missing source: {sum(1 for f in files_info if not f['exists'])}")
    
    # Step 4: Create flat directory
    print(f"\n{'='*70}")
    print("STEP 3: CREATING FLAT DIRECTORY")
    print(f"{'='*70}\n")
    create_flat_directory()
    
    # Step 5: Copy files
    print(f"\n{'='*70}")
    print("STEP 4: COPYING FILES")
    print(f"{'='*70}")
    stats = copy_files(files_info, limit=limit)
    
    # Step 6: Update database
    if not limit:  # Only update DB if processing all files
        print(f"\n{'='*70}")
        print("STEP 5: UPDATING DATABASE")
        print(f"{'='*70}")
        update_database(files_info)
    else:
        print(f"\n[TESTING MODE] Skipping database update (limit={limit})")
    
    # Step 7: Generate report
    report = generate_report(files_info, slug_counts, stats)
    
    # Step 8: Print summary
    print_summary(report)
    
    # Step 9: Next steps
    print(f"\n{'='*70}")
    print("NEXT STEPS")
    print(f"{'='*70}\n")
    
    if DRY_RUN:
        print("✅ This was a DRY RUN. No files were copied or database modified.")
        print("\nTo execute:")
        print("  1. Test with 10 files:   python scripts/23_reorganize_archive.py --live --limit=10")
        print("  2. Test with 100 files:  python scripts/23_reorganize_archive.py --live --limit=100")
        print("  3. Full migration:       python scripts/23_reorganize_archive.py --live")
        print("\nTo skip database backup:")
        print("  python scripts/23_reorganize_archive.py --live --no-backup")
    else:
        print("✅ Reorganization complete!")
        print(f"\nFiles copied to: {NEW_ARCHIVE}")
        print(f"Database updated: {DB_PATH}")
        print(f"Report: {REPORT_PATH}")
        
        if backup_path:
            print(f"\nDatabase backup: {backup_path}")
            print(f"To restore: mv {backup_path} {DB_PATH}")
        
        print("\nNext: Update backend to use flat/ paths")
        print("  See: docs/PHASE11_ARCHIVE_REORGANIZATION.md")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
