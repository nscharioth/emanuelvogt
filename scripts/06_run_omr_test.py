#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Phase 3: Run OMR Test
This script attempts to run batch OMR on the candidate files.
"""

import subprocess
import sys
from pathlib import Path
import os
import shutil

# Define paths
DATA_DIR = Path(__file__).parent.parent / "data"
CANDIDATES_DIR = DATA_DIR / "omr_testing/candidates"
OUTPUT_DIR = DATA_DIR / "omr_testing/outputs"

def check_audiveris():
    """Check if Audiveris command is available."""
    # Check simple command
    if shutil.which("audiveris"):
        return "audiveris"
    
    # Check common locations (MacOS)
    common_paths = [
        Path("/Applications/Audiveris.app/Contents/MacOS/Audiveris"),
        Path("/usr/local/bin/audiveris")
    ]
    
    for p in common_paths:
        if p.exists():
            return str(p)
            
    return None

def main():
    print("="*60)
    print("EMANUEL VOGT ARCHIVE - PHASE 3: OMR TESTING")
    print("="*60)
    
    audiveris_cmd = check_audiveris()
    
    if not audiveris_cmd:
        print("❌ Audiveris command not found.")
        print("Please install Audiveris and ensure it's in your PATH.")
        print("See PHASE3_INSTRUCTIONS.md for details.")
        return
        
    from pdf2image import convert_from_path, pdfinfo_from_path
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None  # Disable decompression bomb warning
    
    # Create temp directory for processed images
    PROCESSED_DIR = DATA_DIR / "omr_testing/processed_candidates"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    files = list(CANDIDATES_DIR.glob("*.pdf"))
    if not files:
        print("❌ No candidate files found in data/omr_testing/candidates/")
        return
    
    print(f"Starting batch processing of {len(files)} files...")
    print(f"Preprocessing (PDF -> Dynamic DPI PNG < 15MP) to respect memory limits...")
    print(f"Output directory: {OUTPUT_DIR}")
    
    for f in files:
        print(f"\nProcessing: {f.name}")
        try:
            # Step 1: Calculate optimal DPI
            try:
                info = pdfinfo_from_path(str(f))
                # extracting page size from pdf info might vary, so let's just use a safe default 
                # or better: use convert_from_path with a size limit? 
                # pdf2image allows size=(width, height) but that might skew aspect ratio if not careful.
                # simpler: convert at low DPI first to get ratio? No, waste of time.
                
                # Let's try 300 DPI first, check size, if too big, downscale
                # Actually, math is safer. Assume A3 (11.7 x 16.5 inches).
                # 15,000,000 = (11.7 * dpi) * (16.5 * dpi) = 193 * dpi^2
                # dpi^2 = 77720 => dpi = 278.
                # So 250 DPI is a safe bet for generic A3.
                # Let's use 250 DPI.
                
                target_dpi = 250 
            except:
                target_dpi = 250

            output_prefix = PROCESSED_DIR / f.stem
            images = convert_from_path(str(f), dpi=target_dpi, fmt="png")
            
            if not images:
                print("❌ Failed to convert PDF to image")
                continue
                
            # Use first page only for this test
            target_image = output_prefix.with_suffix(".png")
            img = images[0]
            
            # Double check size and resize if still too big
            width, height = img.size
            pixels = width * height
            if pixels > 18000000: # 18 MP limit
                scale = (18000000 / pixels) ** 0.5
                new_size = (int(width * scale), int(height * scale))
                print(f"  Resizing from {width}x{height} to {new_size} to fit limits")
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            img.save(target_image)
            print(f"  Converted to PNG: {target_image.name} ({img.size[0]}x{img.size[1]})")
            
            # Step 2: Run Audiveris on the PNG
            # audiveris -batch -export -output <dir> <file>
            cmd = [
                audiveris_cmd,
                "-batch",
                "-export",
                "-output", str(OUTPUT_DIR),
                str(target_image)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Success")
            else:
                print("❌ Failed")
                print(result.stderr)
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
