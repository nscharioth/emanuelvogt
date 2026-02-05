#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Phase 2b: PDF Structure Analysis (No Poppler Required)
This script analyzes PDF structure without converting to images.
"""

import pandas as pd
from pathlib import Path
import PyPDF2
import json

# Define paths
ARCHIVE_ROOT = Path(__file__).parent.parent / "archive"
DATA_DIR = Path(__file__).parent.parent / "data"
QUALITY_DIR = DATA_DIR / "quality_assessment"
OUTPUT_DIR = QUALITY_DIR / "detailed_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

def analyze_pdf_structure(pdf_path):
    """Analyze PDF structure to predict quality."""
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            metrics = {
                'page_count': len(pdf_reader.pages),
                'is_encrypted': pdf_reader.is_encrypted,
                'has_text': False,
                'has_images': False,
                'is_scanned': False,
            }
            
            # Analyze first page
            if len(pdf_reader.pages) > 0:
                page = pdf_reader.pages[0]
                
                # Get page dimensions (in points, 72 points = 1 inch)
                box = page.mediabox
                width_inches = float(box.width) / 72
                height_inches = float(box.height) / 72
                
                metrics['page_width_inches'] = round(width_inches, 2)
                metrics['page_height_inches'] = round(height_inches, 2)
                
                # Try to extract text
                try:
                    text = page.extract_text()
                    metrics['has_text'] = len(text.strip()) > 0
                    metrics['text_length'] = len(text.strip())
                except:
                    metrics['has_text'] = False
                    metrics['text_length'] = 0
                
                # Check for images in page resources
                try:
                    if '/XObject' in page['/Resources']:
                        xobjects = page['/Resources']['/XObject'].get_object()
                        metrics['has_images'] = len(xobjects) > 0
                        metrics['image_count'] = len(xobjects)
                        
                        # If has images but little/no text, likely scanned
                        if metrics['has_images'] and metrics['text_length'] < 50:
                            metrics['is_scanned'] = True
                except:
                    pass
            
            # Get PDF metadata
            if pdf_reader.metadata:
                try:
                    metrics['creator'] = str(pdf_reader.metadata.get('/Creator', ''))
                    metrics['producer'] = str(pdf_reader.metadata.get('/Producer', ''))
                except:
                    pass
            
            return metrics
    
    except Exception as e:
        return {'error': str(e)}

def predict_omr_from_structure(metrics):
    """Predict OMR readiness from PDF structure."""
    if 'error' in metrics:
        return 'Unknown', 'Error during analysis', [metrics['error']]
    
    score = 0
    reasons = []
    
    # Check if it's a scanned document (most music scores are scanned)
    if metrics.get('is_scanned', False):
        score += 1
        reasons.append("Scanned document (typical for music scores)")
    
    # Check page size (A4 is standard for sheet music)
    width = metrics.get('page_width_inches', 0)
    height = metrics.get('page_height_inches', 0)
    
    # A4 is 8.27 x 11.69 inches, Letter is 8.5 x 11
    if 8 <= width <= 9 and 10.5 <= height <= 12:
        score += 1
        reasons.append("Standard page size (A4/Letter)")
    
    # Check for images (scanned music will have images)
    if metrics.get('has_images', False):
        score += 1
        reasons.append(f"Contains {metrics.get('image_count', 0)} image(s)")
    
    # Single page is easier to process
    if metrics.get('page_count', 0) == 1:
        score += 1
        reasons.append("Single page (easier to process)")
    elif metrics.get('page_count', 0) <= 3:
        reasons.append(f"{metrics.get('page_count')} pages")
    
    # Not encrypted is good
    if not metrics.get('is_encrypted', False):
        score += 1
        reasons.append("Not encrypted")
    
    # Determine grade based on structure
    # Note: We can't determine actual image quality without rendering
    if score >= 4:
        grade = 'B'  # Max B without actual image analysis
        prediction = 'Likely suitable for OMR (structure looks good)'
    elif score >= 3:
        grade = 'C'
        prediction = 'May be suitable for OMR (needs testing)'
    else:
        grade = 'D'
        prediction = 'Structure suggests challenges for OMR'
    
    reasons.append("⚠️ Note: Actual image quality unknown without rendering")
    
    return grade, prediction, reasons

def analyze_sample_set():
    """Analyze sample files using PDF structure."""
    
    # Load sample files
    samples_file = QUALITY_DIR / "sample_files.csv"
    if not samples_file.exists():
        print("❌ Error: sample_files.csv not found.")
        return None
    
    df_samples = pd.read_csv(samples_file)
    
    # Select subset - 3 from each range
    df_subset = df_samples.groupby('sample_range', group_keys=False).apply(
        lambda x: x.sample(min(3, len(x)), random_state=42)
    ).reset_index(drop=True)
    
    print(f"\n{'='*60}")
    print(f"Analyzing {len(df_subset)} files (PDF structure)...")
    print(f"{'='*60}\n")
    
    results = []
    
    for idx, row in df_subset.iterrows():
        pdf_path = ARCHIVE_ROOT / row['filepath']
        
        print(f"[{idx+1}/{len(df_subset)}] {row['filename'][:60]}...")
        
        # Analyze PDF structure
        struct_metrics = analyze_pdf_structure(pdf_path)
        
        # Predict OMR readiness
        if 'error' not in struct_metrics:
            grade, prediction, reasons = predict_omr_from_structure(struct_metrics)
        else:
            grade, prediction, reasons = 'Unknown', 'Error', [struct_metrics['error']]
        
        result = {
            'filename': row['filename'],
            'filepath': row['filepath'],
            'work_number': row.get('work_number', 'N/A'),
            'sample_range': row.get('sample_range', 'N/A'),
            'structure_grade': grade,
            'prediction': prediction,
            'reasons': '; '.join(reasons),
            **struct_metrics
        }
        
        results.append(result)
        
        # Print summary
        if 'error' not in struct_metrics:
            print(f"  → Grade: {grade} | Pages: {struct_metrics.get('page_count', 'N/A')} | "
                  f"Scanned: {struct_metrics.get('is_scanned', False)}")
        else:
            print(f"  → Error: {struct_metrics['error']}")
    
    return pd.DataFrame(results)

def generate_report(df_analysis):
    """Generate structure-based quality report."""
    
    report = {
        'total_analyzed': len(df_analysis),
        'grade_distribution': {},
        'scanned_count': 0,
        'avg_pages': 0,
        'encrypted_count': 0,
        'has_images_count': 0,
        'recommendations': []
    }
    
    # Filter out errors
    df_valid = df_analysis[~df_analysis['structure_grade'].isin(['Unknown'])]
    
    if len(df_valid) > 0:
        # Grade distribution
        report['grade_distribution'] = {k: int(v) for k, v in df_valid['structure_grade'].value_counts().to_dict().items()}
        
        # Metrics
        report['scanned_count'] = int(df_valid['is_scanned'].sum()) if 'is_scanned' in df_valid.columns else 0
        report['avg_pages'] = round(float(df_valid['page_count'].mean()), 1) if 'page_count' in df_valid.columns else 0
        report['encrypted_count'] = int(df_valid['is_encrypted'].sum()) if 'is_encrypted' in df_valid.columns else 0
        report['has_images_count'] = int(df_valid['has_images'].sum()) if 'has_images' in df_valid.columns else 0
        
        # Recommendations
        scanned_pct = report['scanned_count'] / len(df_valid) * 100
        
        if scanned_pct >= 80:
            report['recommendations'].append(f"✅ {scanned_pct:.0f}% are scanned documents (typical for music scores)")
        
        if report['has_images_count'] >= len(df_valid) * 0.8:
            report['recommendations'].append("✅ Most files contain images (expected for scanned music)")
        
        if report['encrypted_count'] == 0:
            report['recommendations'].append("✅ No encrypted files (good for processing)")
        
        report['recommendations'].append("⚠️ Install poppler to analyze actual image quality (DPI, contrast)")
        report['recommendations'].append("💡 Test sample files with OMR software (Audiveris, MuseScore) to confirm quality")
    
    return report

def main():
    """Main analysis process."""
    print("\n" + "="*60)
    print("EMANUEL VOGT ARCHIVE - PDF STRUCTURE ANALYSIS")
    print("(Alternative approach - no poppler required)")
    print("="*60)
    
    # Analyze PDF structure
    df_analysis = analyze_sample_set()
    
    if df_analysis is None:
        return
    
    # Save analysis
    analysis_file = OUTPUT_DIR / "pdf_structure_analysis.csv"
    df_analysis.to_csv(analysis_file, index=False)
    print(f"\n✅ Saved analysis: {analysis_file}")
    
    # Generate report
    print(f"\n{'='*60}")
    print("GENERATING REPORT")
    print(f"{'='*60}")
    
    report = generate_report(df_analysis)
    
    report_file = OUTPUT_DIR / "structure_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ Saved report: {report_file}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("PDF STRUCTURE ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Files analyzed: {report['total_analyzed']}")
    
    print(f"\n📊 Structure Grade Distribution:")
    for grade in ['B', 'C', 'D']:
        count = report['grade_distribution'].get(grade, 0)
        if count > 0:
            pct = count / report['total_analyzed'] * 100
            print(f"  Grade {grade}: {count} files ({pct:.1f}%)")
    
    print(f"\n📏 Structure Metrics:")
    print(f"  Scanned documents: {report['scanned_count']}/{report['total_analyzed']}")
    print(f"  Files with images: {report['has_images_count']}/{report['total_analyzed']}")
    print(f"  Average pages: {report['avg_pages']}")
    print(f"  Encrypted files: {report['encrypted_count']}")
    
    print(f"\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("1. Wait for poppler installation to complete")
    print("2. Run 03_enhanced_quality_analysis.py for full image analysis")
    print("3. Or proceed with manual OMR testing on sample files")
    print("4. Check if Audiveris or MuseScore is available on your system")

if __name__ == "__main__":
    main()
