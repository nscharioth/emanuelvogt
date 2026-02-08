#!/usr/bin/env python3
"""
Script 20: Analyze PDF Content Rotation (Image-Based)
Analyzes actual content orientation by checking image dimensions within PDFs.
"""

import sqlite3
import os
from pathlib import Path
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image
import json
from collections import Counter
import io

def analyze_pdf_content_orientation(db_path, archive_root, sample_size=100):
    """
    Analyze PDF content orientation by converting first page to image
    and checking actual pixel dimensions.
    """
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all PDF files
    cursor.execute("""
        SELECT f.id, f.work_id, f.filepath, w.work_number, w.title
        FROM files f
        JOIN works w ON f.work_id = w.id
        WHERE f.file_type = 'pdf'
        ORDER BY f.work_id
    """)
    
    files = cursor.fetchall()
    print(f"Found {len(files)} PDF files")
    print(f"Analyzing sample of {min(sample_size, len(files))} files...\n")
    
    results = {
        'total_files': len(files),
        'analyzed': 0,
        'errors': 0,
        'likely_rotated': [],
        'orientation_stats': Counter(),
        'error_files': []
    }
    
    # Analyze sample
    sample = files[:sample_size] if sample_size else files
    
    for file_id, work_id, filepath, work_number, title in sample:
        full_path = os.path.join(archive_root, filepath)
        
        if not os.path.exists(full_path):
            results['errors'] += 1
            results['error_files'].append({
                'file_id': file_id,
                'work_number': work_number,
                'title': title,
                'error': 'File not found'
            })
            continue
        
        try:
            # Convert first page to image
            images = convert_from_path(full_path, first_page=1, last_page=1, dpi=72)
            
            if images:
                img = images[0]
                width, height = img.size
                
                # Determine if content looks rotated
                # For sheet music, we expect portrait (height > width)
                aspect_ratio = width / height
                
                if width > height * 1.2:  # Clearly landscape
                    orientation = 'landscape'
                    likely_rotated = True  # Sheet music should be portrait
                elif height > width * 1.2:  # Clearly portrait
                    orientation = 'portrait'
                    likely_rotated = False
                else:  # Nearly square
                    orientation = 'square'
                    likely_rotated = False
                
                results['orientation_stats'][orientation] += 1
                results['analyzed'] += 1
                
                if likely_rotated:
                    results['likely_rotated'].append({
                        'file_id': file_id,
                        'work_number': work_number,
                        'title': title,
                        'filepath': filepath,
                        'dimensions': f"{width}x{height}",
                        'aspect_ratio': f"{aspect_ratio:.2f}",
                        'orientation': orientation
                    })
                
                # Progress
                if results['analyzed'] % 10 == 0:
                    print(f"  Analyzed {results['analyzed']}/{len(sample)} files... "
                          f"(Found {len(results['likely_rotated'])} rotated)")
        
        except Exception as e:
            results['errors'] += 1
            results['error_files'].append({
                'file_id': file_id,
                'work_number': work_number,
                'title': title,
                'error': str(e)
            })
    
    conn.close()
    
    # Print summary
    print("\n" + "="*80)
    print("PDF CONTENT ORIENTATION ANALYSIS")
    print("="*80)
    print(f"\nAnalyzed: {results['analyzed']} files")
    print(f"Errors: {results['errors']}")
    
    print("\n--- Orientation Statistics ---")
    for orientation, count in sorted(results['orientation_stats'].items()):
        percentage = (count / results['analyzed'] * 100) if results['analyzed'] > 0 else 0
        print(f"  {orientation}: {count} files ({percentage:.1f}%)")
    
    print(f"\n--- Likely Rotated Files (Landscape) ---")
    print(f"Total: {len(results['likely_rotated'])} files")
    
    if results['likely_rotated']:
        print("\nExamples:")
        for i, file_info in enumerate(results['likely_rotated'][:20], 1):
            print(f"\n  {i}. {file_info['work_number']} - {file_info['title']}")
            print(f"     Dimensions: {file_info['dimensions']} (aspect: {file_info['aspect_ratio']})")
            print(f"     Path: {file_info['filepath']}")
    
    # Save results
    output_file = 'data/pdf_content_rotation_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to: {output_file}")
    print("="*80)
    
    return results

if __name__ == "__main__":
    db_path = "data/archive.db"
    archive_root = "archive"
    
    # Analyze first 100 files as sample, or set to None for all files
    sample_size = 200
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        exit(1)
    
    analyze_pdf_content_orientation(db_path, archive_root, sample_size)
