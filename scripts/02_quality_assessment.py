#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Step 2: Quality Assessment
This script analyzes PDF quality and generates a sample set for OMR testing.
"""

import pandas as pd
from pathlib import Path
import PyPDF2
import random
import json

# Define paths
ARCHIVE_ROOT = Path(__file__).parent.parent / "archive"
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "quality_assessment"
OUTPUT_DIR.mkdir(exist_ok=True)

def analyze_pdf_metadata(pdf_path):
    """Extract metadata from a PDF file."""
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            metadata = {
                'page_count': len(pdf_reader.pages),
                'is_encrypted': pdf_reader.is_encrypted,
                'metadata': {}
            }
            
            # Get PDF metadata
            if pdf_reader.metadata:
                for key, value in pdf_reader.metadata.items():
                    metadata['metadata'][key] = str(value)
            
            # Try to get first page dimensions
            if len(pdf_reader.pages) > 0:
                page = pdf_reader.pages[0]
                box = page.mediabox
                metadata['page_width'] = float(box.width)
                metadata['page_height'] = float(box.height)
            
            return metadata
    
    except Exception as e:
        return {'error': str(e)}

def select_representative_samples(df_files, n_samples=50):
    """Select representative sample of works for quality testing."""
    
    # Filter to PDF files only
    df_pdf = df_files[df_files['file_type'] == 'pdf'].copy()
    
    # Extract numeric work number for sorting
    df_pdf['work_num'] = df_pdf['work_number'].str.extract(r'(\d+)').astype(float)
    
    # Define ranges for sampling
    ranges = [
        ('Early Works', 0, 100),
        ('Werke 1-400', 1, 400),
        ('Werke 401-800', 401, 800),
        ('Werke 801-1200', 801, 1200),
        ('Werke 1201-1711', 1201, 2000)
    ]
    
    samples = []
    samples_per_range = n_samples // len(ranges)
    
    for range_name, min_num, max_num in ranges:
        range_files = df_pdf[
            (df_pdf['work_num'] >= min_num) & 
            (df_pdf['work_num'] < max_num)
        ]
        
        if len(range_files) > 0:
            n_to_sample = min(samples_per_range, len(range_files))
            sampled = range_files.sample(n=n_to_sample, random_state=42)
            sampled['sample_range'] = range_name
            samples.append(sampled)
    
    df_samples = pd.concat(samples, ignore_index=True)
    return df_samples

def assess_pdf_quality(df_samples, archive_root):
    """Assess quality of sampled PDF files."""
    
    results = []
    
    print(f"\n{'='*60}")
    print(f"Assessing {len(df_samples)} PDF samples...")
    print(f"{'='*60}\n")
    
    for idx, row in df_samples.iterrows():
        pdf_path = archive_root / row['filepath']
        
        print(f"[{idx+1}/{len(df_samples)}] {row['filename'][:50]}...")
        
        metadata = analyze_pdf_metadata(pdf_path)
        
        result = {
            'filename': row['filename'],
            'filepath': row['filepath'],
            'work_number': row['work_number'],
            'sample_range': row['sample_range'],
            'file_size_mb': row['file_size_mb'],
            **metadata
        }
        
        results.append(result)
    
    return pd.DataFrame(results)

def generate_quality_report(df_quality):
    """Generate summary quality report."""
    
    report = {
        'total_samples': int(len(df_quality)),
        'avg_page_count': float(df_quality['page_count'].mean()) if 'page_count' in df_quality else 0,
        'max_page_count': int(df_quality['page_count'].max()) if 'page_count' in df_quality else 0,
        'min_page_count': int(df_quality['page_count'].min()) if 'page_count' in df_quality else 0,
        'encrypted_count': int(df_quality['is_encrypted'].sum()) if 'is_encrypted' in df_quality else 0,
        'errors_count': int(df_quality['error'].notna().sum()) if 'error' in df_quality else 0,
        'avg_file_size_mb': float(df_quality['file_size_mb'].mean()),
        'samples_by_range': {k: int(v) for k, v in df_quality['sample_range'].value_counts().to_dict().items()}
    }
    
    return report

def main():
    """Main quality assessment process."""
    print("\n" + "="*60)
    print("EMANUEL VOGT ARCHIVE - QUALITY ASSESSMENT")
    print("="*60)
    
    # Load file inventory
    inventory_file = DATA_DIR / "file_inventory.csv"
    if not inventory_file.exists():
        print("❌ Error: file_inventory.csv not found. Run 01_consolidate_catalogs.py first.")
        return
    
    df_files = pd.read_csv(inventory_file)
    print(f"\n📁 Loaded {len(df_files)} files from inventory")
    
    # Step 1: Select representative samples
    print(f"\n{'='*60}")
    print("Step 1: Selecting Representative Samples")
    print(f"{'='*60}")
    
    df_samples = select_representative_samples(df_files, n_samples=50)
    print(f"\n✅ Selected {len(df_samples)} samples")
    print(f"\n📊 Distribution by range:")
    print(df_samples['sample_range'].value_counts())
    
    # Save sample list
    samples_file = OUTPUT_DIR / "sample_files.csv"
    df_samples.to_csv(samples_file, index=False)
    print(f"\n✅ Saved sample list: {samples_file}")
    
    # Step 2: Assess PDF quality
    print(f"\n{'='*60}")
    print("Step 2: Assessing PDF Quality")
    print(f"{'='*60}")
    
    df_quality = assess_pdf_quality(df_samples, ARCHIVE_ROOT)
    
    # Save quality assessment
    quality_file = OUTPUT_DIR / "pdf_quality_assessment.csv"
    df_quality.to_csv(quality_file, index=False)
    print(f"\n✅ Saved quality assessment: {quality_file}")
    
    # Step 3: Generate report
    print(f"\n{'='*60}")
    print("Step 3: Generating Quality Report")
    print(f"{'='*60}")
    
    report = generate_quality_report(df_quality)
    
    report_file = OUTPUT_DIR / "quality_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ Saved quality report: {report_file}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("QUALITY ASSESSMENT SUMMARY")
    print(f"{'='*60}")
    print(f"Total samples analyzed: {report['total_samples']}")
    print(f"Average page count: {report['avg_page_count']:.1f}")
    print(f"Page count range: {report['min_page_count']:.0f} - {report['max_page_count']:.0f}")
    print(f"Encrypted PDFs: {report['encrypted_count']}")
    print(f"Errors encountered: {report['errors_count']}")
    print(f"Average file size: {report['avg_file_size_mb']:.2f} MB")
    
    print(f"\n💡 Next steps:")
    print(f"  1. Review sample files in: {samples_file}")
    print(f"  2. Test selected samples with OMR software (Audiveris, MuseScore)")
    print(f"  3. Manually grade quality (A/B/C/D) for each sample")
    print(f"  4. Update pdf_quality_assessment.csv with quality grades")
    print(f"  5. Extrapolate findings to full catalog")

if __name__ == "__main__":
    main()
