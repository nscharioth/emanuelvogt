#!/usr/bin/env python3
"""
Script 19: Analyze PDF Rotation
Analyzes all PDFs in the archive to detect rotation issues.
"""

import sqlite3
import os
from pathlib import Path
import PyPDF2
import json
from collections import Counter

def analyze_pdf_rotation(db_path, archive_root):
    """Analyze rotation of all PDFs in the archive."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all PDF files
    cursor.execute("""
        SELECT id, work_id, filepath
        FROM files
        WHERE file_type = 'pdf'
        ORDER BY work_id
    """)
    
    files = cursor.fetchall()
    print(f"Analyzing {len(files)} PDF files...\n")
    
    results = {
        'total_files': len(files),
        'analyzed': 0,
        'errors': 0,
        'rotation_stats': Counter(),
        'rotated_files': [],
        'error_files': []
    }
    
    for file_id, work_id, file_path in files:
        full_path = os.path.join(archive_root, file_path)
        
        if not os.path.exists(full_path):
            results['errors'] += 1
            results['error_files'].append({
                'file_id': file_id,
                'work_id': work_id,
                'path': file_path,
                'error': 'File not found'
            })
            continue
        
        try:
            with open(full_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                
                # Analyze first page (most representative)
                if len(pdf.pages) > 0:
                    page = pdf.pages[0]
                    
                    # Get rotation
                    rotation = page.get('/Rotate', 0)
                    
                    # Get dimensions
                    mediabox = page.mediabox
                    width = float(mediabox.width)
                    height = float(mediabox.height)
                    
                    # Determine orientation
                    if width > height:
                        orientation = 'landscape'
                    else:
                        orientation = 'portrait'
                    
                    results['rotation_stats'][rotation] += 1
                    results['analyzed'] += 1
                    
                    # Flag files with non-zero rotation
                    if rotation != 0:
                        results['rotated_files'].append({
                            'file_id': file_id,
                            'work_id': work_id,
                            'path': file_path,
                            'rotation': rotation,
                            'orientation': orientation,
                            'dimensions': f"{width:.1f}x{height:.1f}",
                            'pages': len(pdf.pages)
                        })
                    
                    # Progress indicator
                    if results['analyzed'] % 100 == 0:
                        print(f"  Analyzed {results['analyzed']}/{len(files)} files...")
        
        except Exception as e:
            results['errors'] += 1
            results['error_files'].append({
                'file_id': file_id,
                'work_id': work_id,
                'path': file_path,
                'error': str(e)
            })
    
    conn.close()
    
    # Print summary
    print("\n" + "="*80)
    print("PDF ROTATION ANALYSIS SUMMARY")
    print("="*80)
    print(f"\nTotal files: {results['total_files']}")
    print(f"Successfully analyzed: {results['analyzed']}")
    print(f"Errors: {results['errors']}")
    
    print("\n--- Rotation Statistics ---")
    for rotation, count in sorted(results['rotation_stats'].items()):
        percentage = (count / results['analyzed'] * 100) if results['analyzed'] > 0 else 0
        print(f"  {rotation}° rotation: {count} files ({percentage:.1f}%)")
    
    print(f"\n--- Files with Non-Zero Rotation ---")
    print(f"Total: {len(results['rotated_files'])} files")
    
    if results['rotated_files']:
        print("\nFirst 10 examples:")
        for i, file_info in enumerate(results['rotated_files'][:10], 1):
            print(f"\n  {i}. {file_info['work_id']} - {file_info['rotation']}°")
            print(f"     Path: {file_info['path']}")
            print(f"     Orientation: {file_info['orientation']}, Dimensions: {file_info['dimensions']}, Pages: {file_info['pages']}")
    
    if results['errors'] > 0:
        print(f"\n--- Errors ({results['errors']} files) ---")
        for i, error in enumerate(results['error_files'][:5], 1):
            print(f"  {i}. {error['work_id']}: {error['error']}")
        if len(results['error_files']) > 5:
            print(f"  ... and {len(results['error_files']) - 5} more")
    
    # Save detailed results
    output_file = 'data/pdf_rotation_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Detailed results saved to: {output_file}")
    print("="*80)
    
    return results

if __name__ == "__main__":
    db_path = "data/archive.db"
    archive_root = "archive"  # Paths in DB already include 'files/'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        exit(1)
    
    analyze_pdf_rotation(db_path, archive_root)
