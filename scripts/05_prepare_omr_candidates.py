#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Phase 3: Archive Grade A Candidates
This script copies the best OMR candidates to a dedicated folder for testing.
"""

import pandas as pd
from pathlib import Path
import shutil
import sys

# Define paths
ARCHIVE_ROOT = Path(__file__).parent.parent / "archive"
DATA_DIR = Path(__file__).parent.parent / "data"
ANALYSIS_FILE = DATA_DIR / "quality_assessment/detailed_analysis/detailed_image_analysis.csv"
TARGET_DIR = DATA_DIR / "omr_testing/candidates"

def main():
    print(f"Loading analysis from: {ANALYSIS_FILE}")
    if not ANALYSIS_FILE.exists():
        print("❌ Analysis file not found. Run Phase 2 scripts first.")
        return

    df = pd.read_csv(ANALYSIS_FILE)
    
    # Filter for Grade A files
    grade_a = df[df['omr_grade'] == 'A']
    print(f"Found {len(grade_a)} Grade A candidates.")
    
    if len(grade_a) == 0:
        print("No Grade A files found. Checking Grade B...")
        grade_a = df[df['omr_grade'] == 'B']
        print(f"Found {len(grade_a)} Grade B candidates.")

    # TARGET_DIR.mkdir(exist_ok=True, parents=True) # created by tool
    
    count = 0
    for idx, row in grade_a.iterrows():
        source_path = ARCHIVE_ROOT / row['filepath']
        
        # Create a safe filename (keep original name but ensure it's safe)
        safe_name = Path(row['filename']).name
        target_path = TARGET_DIR / safe_name
        
        if source_path.exists():
            print(f"Copying: {safe_name}")
            shutil.copy2(source_path, target_path)
            count += 1
        else:
            print(f"⚠️ Source file missing: {source_path}")
            
    print(f"\n✅ Copied {count} files to {TARGET_DIR}")
    print("These files are ready for manual or automated OMR testing.")

if __name__ == "__main__":
    main()
