#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Step 1: Catalog Consolidation
This script consolidates all Excel catalogs into a unified CSV database.
"""

import pandas as pd
import os
from pathlib import Path
import json

# Define paths
ARCHIVE_ROOT = Path(__file__).parent.parent / "archive"
FILES_DIR = ARCHIVE_ROOT / "files"
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

# Excel catalog files
EXCEL_CATALOGS = {
    "main_work_list": FILES_DIR / "Werke - außer Psalmen" / "2026-01-06  Liste kompositorisches Werk - Endfassung.xlsx",
    "gema_list": FILES_DIR / "2025-11-04 GEMA-Liste Emanuel Vogt.xlsx",
    "werke_list": FILES_DIR / "Werke_03-11-2025_9004011966_9004063322.xlsx",
    "psalmen_list": FILES_DIR / "Psalmen" / "2025-10-07 Psalmenaufstellung E. Vogt - Gesamt^LJ Strube^LJ Unveröffentlicht.xlsx"
}

def load_excel_catalog(filepath, catalog_name):
    """Load an Excel catalog and return DataFrame with metadata."""
    print(f"\n{'='*60}")
    print(f"Loading: {catalog_name}")
    print(f"File: {filepath.name}")
    print(f"{'='*60}")
    
    if not filepath.exists():
        print(f"⚠️  File not found: {filepath}")
        return None
    
    try:
        # Try to read the Excel file
        xl_file = pd.ExcelFile(filepath)
        print(f"📊 Sheets found: {xl_file.sheet_names}")
        
        # Read all sheets
        sheets = {}
        for sheet_name in xl_file.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            sheets[sheet_name] = df
            print(f"\n  Sheet: '{sheet_name}'")
            print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
            print(f"  Columns: {list(df.columns)[:10]}")  # First 10 columns
            
        return sheets
    
    except Exception as e:
        print(f"❌ Error loading {catalog_name}: {e}")
        return None

def analyze_file_system():
    """Scan the archive file system and create inventory."""
    print(f"\n{'='*60}")
    print("Analyzing File System")
    print(f"{'='*60}")
    
    file_inventory = []
    
    # Scan Werke - außer Psalmen
    werke_dir = FILES_DIR / "Werke - außer Psalmen"
    if werke_dir.exists():
        for folder in sorted(werke_dir.iterdir()):
            if folder.is_dir():
                for file in folder.iterdir():
                    if file.suffix.lower() in ['.pdf', '.jpg', '.png']:
                        file_inventory.append({
                            'category': 'Werke',
                            'folder': folder.name,
                            'filename': file.name,
                            'filepath': str(file.relative_to(ARCHIVE_ROOT)),
                            'file_type': file.suffix.lower()[1:],
                            'file_size_bytes': file.stat().st_size,
                            'file_size_mb': round(file.stat().st_size / (1024*1024), 2)
                        })
    
    # Scan Psalmen
    psalmen_dir = FILES_DIR / "Psalmen"
    if psalmen_dir.exists():
        for root, dirs, files in os.walk(psalmen_dir):
            for file in files:
                filepath = Path(root) / file
                if filepath.suffix.lower() in ['.pdf', '.jpg', '.png']:
                    file_inventory.append({
                        'category': 'Psalmen',
                        'folder': Path(root).relative_to(psalmen_dir).parts[0] if Path(root) != psalmen_dir else 'root',
                        'filename': file,
                        'filepath': str(filepath.relative_to(ARCHIVE_ROOT)),
                        'file_type': filepath.suffix.lower()[1:],
                        'file_size_bytes': filepath.stat().st_size,
                        'file_size_mb': round(filepath.stat().st_size / (1024*1024), 2)
                    })
    
    df_files = pd.DataFrame(file_inventory)
    
    print(f"\n📁 Total files found: {len(df_files)}")
    print(f"\n📊 By file type:")
    print(df_files['file_type'].value_counts())
    print(f"\n📊 By category:")
    print(df_files['category'].value_counts())
    print(f"\n💾 Total size: {df_files['file_size_mb'].sum():.2f} MB")
    
    return df_files

def extract_work_number(filename):
    """Extract work number from filename."""
    import re
    # Pattern: starts with digits, optionally followed by letter
    match = re.match(r'^(\d+[a-z]?)', filename)
    if match:
        return match.group(1)
    return None

def main():
    """Main consolidation process."""
    print("\n" + "="*60)
    print("EMANUEL VOGT ARCHIVE - CATALOG CONSOLIDATION")
    print("="*60)
    
    # Step 1: Load all Excel catalogs
    all_catalogs = {}
    for catalog_name, filepath in EXCEL_CATALOGS.items():
        sheets = load_excel_catalog(filepath, catalog_name)
        if sheets:
            all_catalogs[catalog_name] = sheets
    
    # Step 2: Analyze file system
    df_files = analyze_file_system()
    
    # Step 3: Extract work numbers from filenames
    df_files['work_number'] = df_files['filename'].apply(extract_work_number)
    
    # Step 4: Save outputs
    print(f"\n{'='*60}")
    print("Saving Outputs")
    print(f"{'='*60}")
    
    # Save file inventory
    output_file = OUTPUT_DIR / "file_inventory.csv"
    df_files.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✅ Saved: {output_file}")
    
    # Save each Excel catalog as CSV
    for catalog_name, sheets in all_catalogs.items():
        for sheet_name, df in sheets.items():
            safe_sheet_name = sheet_name.replace(' ', '_').replace('/', '_')
            output_file = OUTPUT_DIR / f"{catalog_name}_{safe_sheet_name}.csv"
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"✅ Saved: {output_file}")
    
    # Step 5: Generate summary report
    summary = {
        'total_files': len(df_files),
        'pdf_count': len(df_files[df_files['file_type'] == 'pdf']),
        'jpg_count': len(df_files[df_files['file_type'] == 'jpg']),
        'png_count': len(df_files[df_files['file_type'] == 'png']),
        'total_size_mb': float(df_files['file_size_mb'].sum()),
        'werke_count': len(df_files[df_files['category'] == 'Werke']),
        'psalmen_count': len(df_files[df_files['category'] == 'Psalmen']),
        'unique_work_numbers': df_files['work_number'].nunique(),
        'catalogs_processed': list(all_catalogs.keys())
    }
    
    summary_file = OUTPUT_DIR / "consolidation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved: {summary_file}")
    
    print(f"\n{'='*60}")
    print("CONSOLIDATION COMPLETE")
    print(f"{'='*60}")
    print(f"📊 Summary:")
    for key, value in summary.items():
        if key != 'catalogs_processed':
            print(f"  {key}: {value}")
    
    print(f"\n💡 Next steps:")
    print(f"  1. Review CSV files in: {OUTPUT_DIR}")
    print(f"  2. Cross-reference work numbers across catalogs")
    print(f"  3. Identify gaps and duplicates")
    print(f"  4. Run quality assessment script")

if __name__ == "__main__":
    main()
