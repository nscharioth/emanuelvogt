#!/usr/bin/env python3
"""
Script 21: Analyze PDF Content Rotation (Direct Image Extraction)
Analyzes actual content orientation by extracting embedded images from PDFs.
"""

import sqlite3
import os
import PyPDF2
import json
from collections import Counter

def analyze_pdf_images(db_path, archive_root, sample_size=None):
    """
    Analyze PDF content by extracting image dimensions directly from PDF.
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
    total = len(files)
    
    if sample_size:
        files = files[:sample_size]
    
    print(f"Analyzing {len(files)} PDF files (of {total} total)...\n")
    
    results = {
        'total_files': total,
        'analyzed': 0,
        'errors': 0,
        'likely_rotated': [],
        'orientation_stats': Counter(),
        'error_files': []
    }
    
    for file_id, work_id, filepath, work_number, title in files:
        full_path = os.path.join(archive_root, filepath)
        
        if not os.path.exists(full_path):
            results['errors'] += 1
            continue
        
        try:
            with open(full_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                
                if len(pdf.pages) == 0:
                    results['errors'] += 1
                    continue
                
                page = pdf.pages[0]
                
                # Get page dimensions (after any PDF rotation)
                mediabox = page.mediabox
                page_width = float(mediabox.width)
                page_height = float(mediabox.height)
                
                # Check PDF rotation
                pdf_rotation = page.get('/Rotate', 0)
                
                # Adjust dimensions based on PDF rotation
                if pdf_rotation in [90, 270]:
                    page_width, page_height = page_height, page_width
                
                # Determine orientation
                aspect_ratio = page_width / page_height
                
                if page_width > page_height * 1.15:  # Landscape
                    orientation = 'landscape'
                    likely_rotated = True  # Sheet music should typically be portrait
                elif page_height > page_width * 1.15:  # Portrait
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
                        'dimensions': f"{page_width:.0f}x{page_height:.0f}",
                        'aspect_ratio': f"{aspect_ratio:.2f}",
                        'pdf_rotation': pdf_rotation,
                        'orientation': orientation
                    })
                
                # Progress
                if results['analyzed'] % 100 == 0:
                    print(f"  Analyzed {results['analyzed']}/{len(files)} files... "
                          f"(Found {len(results['likely_rotated'])} landscape)")
        
        except Exception as e:
            results['errors'] += 1
            results['error_files'].append({
                'work_number': work_number,
                'title': title,
                'error': str(e)[:100]
            })
    
    conn.close()
    
    # Print summary
    print("\n" + "="*80)
    print("PDF CONTENT ORIENTATION ANALYSIS")
    print("="*80)
    print(f"\nTotal files: {results['total_files']}")
    print(f"Analyzed: {results['analyzed']}")
    print(f"Errors: {results['errors']}")
    
    print("\n--- Orientation Statistics ---")
    for orientation, count in sorted(results['orientation_stats'].items()):
        percentage = (count / results['analyzed'] * 100) if results['analyzed'] > 0 else 0
        print(f"  {orientation}: {count} files ({percentage:.1f}%)")
    
    print(f"\n--- Likely Rotated Files (Landscape Orientation) ---")
    print(f"Total: {len(results['likely_rotated'])} files")
    print(f"Percentage: {len(results['likely_rotated'])/results['analyzed']*100:.1f}%")
    
    if results['likely_rotated']:
        print("\nFirst 30 examples:")
        for i, file_info in enumerate(results['likely_rotated'][:30], 1):
            print(f"  {i}. {file_info['work_number']} - {file_info['title']}")
            print(f"     Dims: {file_info['dimensions']}, Aspect: {file_info['aspect_ratio']}, PDF Rot: {file_info['pdf_rotation']}°")
    
    if results['errors'] > 0:
        print(f"\n--- Errors: {results['errors']} files ---")
        for i, err in enumerate(results['error_files'][:5], 1):
            print(f"  {i}. {err['work_number']} - {err.get('title', 'N/A')}: {err['error']}")
    
    # Save results
    output_file = 'data/pdf_landscape_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to: {output_file}")
    print("="*80)
    
    return results

if __name__ == "__main__":
    db_path = "data/archive.db"
    archive_root = "archive"
    
    # Set to None to analyze all files
    sample_size = None
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        exit(1)
    
    analyze_pdf_images(db_path, archive_root, sample_size)
