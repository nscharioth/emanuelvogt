#!/usr/bin/env python3
"""
Emanuel Vogt Archive - Phase 2: Enhanced Image Quality Analysis
This script performs detailed image quality analysis to predict OMR readiness.
"""

import pandas as pd
from pathlib import Path
import PyPDF2
from PIL import Image
import pdf2image
import numpy as np
import json
import sys

# Define paths
ARCHIVE_ROOT = Path(__file__).parent.parent / "archive"
DATA_DIR = Path(__file__).parent.parent / "data"
QUALITY_DIR = DATA_DIR / "quality_assessment"
OUTPUT_DIR = QUALITY_DIR / "detailed_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

def analyze_image_quality(image):
    """Analyze image quality metrics relevant for OMR."""
    # Convert to numpy array
    img_array = np.array(image)
    
    # Get image dimensions
    height, width = img_array.shape[:2]
    
    # Calculate DPI estimate (assuming standard page size)
    # A4 page is 8.27 x 11.69 inches
    dpi_estimate = max(width / 8.27, height / 11.69)
    
    # Convert to grayscale for analysis
    if len(img_array.shape) == 3:
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array
    
    # Calculate quality metrics
    metrics = {
        'width': int(width),
        'height': int(height),
        'dpi_estimate': round(dpi_estimate, 1),
        'mean_brightness': round(float(np.mean(gray)), 2),
        'std_brightness': round(float(np.std(gray)), 2),
        'contrast_ratio': round(float(np.max(gray) - np.min(gray)), 2),
        'is_color': len(img_array.shape) == 3 and img_array.shape[2] > 1,
    }
    
    # Estimate quality grade based on DPI
    if dpi_estimate >= 300:
        metrics['dpi_grade'] = 'A'
    elif dpi_estimate >= 200:
        metrics['dpi_grade'] = 'B'
    elif dpi_estimate >= 150:
        metrics['dpi_grade'] = 'C'
    else:
        metrics['dpi_grade'] = 'D'
    
    # Estimate contrast quality
    if metrics['contrast_ratio'] > 200:
        metrics['contrast_grade'] = 'A'
    elif metrics['contrast_ratio'] > 150:
        metrics['contrast_grade'] = 'B'
    elif metrics['contrast_ratio'] > 100:
        metrics['contrast_grade'] = 'C'
    else:
        metrics['contrast_grade'] = 'D'
    
    return metrics

def analyze_pdf_images(pdf_path, max_pages=3):
    """Extract and analyze images from PDF."""
    try:
        # Convert first few pages to images
        images = pdf2image.convert_from_path(
            pdf_path, 
            dpi=150,  # Lower DPI for analysis speed
            first_page=1,
            last_page=min(max_pages, 3)
        )
        
        if not images:
            return {'error': 'No images extracted'}
        
        # Analyze first page (most representative)
        first_page_metrics = analyze_image_quality(images[0])
        
        # Add page count
        first_page_metrics['pages_analyzed'] = len(images)
        
        return first_page_metrics
        
    except Exception as e:
        return {'error': str(e)}

def predict_omr_readiness(metrics):
    """Predict OMR readiness based on quality metrics."""
    if 'error' in metrics:
        return 'Unknown', 'Error during analysis'
    
    dpi = metrics.get('dpi_estimate', 0)
    contrast = metrics.get('contrast_ratio', 0)
    
    # Scoring system
    score = 0
    reasons = []
    
    # DPI scoring
    if dpi >= 300:
        score += 3
        reasons.append("Excellent resolution (≥300 DPI)")
    elif dpi >= 200:
        score += 2
        reasons.append("Good resolution (≥200 DPI)")
    elif dpi >= 150:
        score += 1
        reasons.append("Acceptable resolution (≥150 DPI)")
    else:
        reasons.append("Low resolution (<150 DPI)")
    
    # Contrast scoring
    if contrast > 200:
        score += 2
        reasons.append("Excellent contrast")
    elif contrast > 150:
        score += 1
        reasons.append("Good contrast")
    else:
        reasons.append("Low contrast")
    
    # Determine grade
    if score >= 4:
        grade = 'A'
        prediction = 'Excellent OMR candidate'
    elif score >= 3:
        grade = 'B'
        prediction = 'Good OMR candidate'
    elif score >= 2:
        grade = 'C'
        prediction = 'May require preprocessing'
    else:
        grade = 'D'
        prediction = 'Manual transcription likely needed'
    
    return grade, prediction, reasons

def analyze_sample_set(sample_size=15):
    """Analyze a subset of the sample files in detail."""
    
    # Load sample files
    samples_file = QUALITY_DIR / "sample_files.csv"
    if not samples_file.exists():
        print("❌ Error: sample_files.csv not found. Run 02_quality_assessment.py first.")
        return None
    
    df_samples = pd.read_csv(samples_file)
    
    # Select subset for detailed analysis
    if len(df_samples) > sample_size:
        # Stratified sampling - 3 from each range
        df_subset = df_samples.groupby('sample_range', group_keys=False).apply(
            lambda x: x.sample(min(3, len(x)), random_state=42)
        )
    else:
        df_subset = df_samples
    
    print(f"\n{'='*60}")
    print(f"Analyzing {len(df_subset)} files in detail...")
    print(f"{'='*60}\n")
    
    results = []
    
    for idx, row in df_subset.reset_index(drop=True).iterrows():
        pdf_path = ARCHIVE_ROOT / row['filepath']
        
        print(f"[{idx+1}/{len(df_subset)}] {row['filename'][:60]}...")
        
        # Analyze PDF images
        image_metrics = analyze_pdf_images(pdf_path)
        
        # Predict OMR readiness
        if 'error' not in image_metrics:
            grade, prediction, reasons = predict_omr_readiness(image_metrics)
        else:
            grade, prediction, reasons = 'Unknown', 'Error', [image_metrics['error']]
        
        result = {
            'filename': row['filename'],
            'filepath': row['filepath'],
            'work_number': row.get('work_number', 'N/A'),
            'sample_range': row.get('sample_range', 'N/A'),
            'omr_grade': grade,
            'omr_prediction': prediction,
            'omr_reasons': '; '.join(reasons),
            **image_metrics
        }
        
        results.append(result)
        
        # Print summary
        if 'error' not in image_metrics:
            print(f"  → Grade: {grade} | DPI: {image_metrics.get('dpi_estimate', 'N/A')} | "
                  f"Contrast: {image_metrics.get('contrast_ratio', 'N/A')}")
        else:
            print(f"  → Error: {image_metrics['error']}")
    
    return pd.DataFrame(results)

def generate_detailed_report(df_analysis):
    """Generate detailed quality report with OMR predictions."""
    
    report = {
        'total_analyzed': len(df_analysis),
        'omr_grade_distribution': {},
        'avg_dpi': 0,
        'avg_contrast': 0,
        'color_vs_bw': {},
        'recommendations': []
    }
    
    # Filter out errors
    df_valid = df_analysis[~df_analysis['omr_grade'].isin(['Unknown'])]
    
    if len(df_valid) > 0:
        # Grade distribution
        report['omr_grade_distribution'] = df_valid['omr_grade'].value_counts().to_dict()
        
        # Average metrics
        if 'dpi_estimate' in df_valid.columns:
            report['avg_dpi'] = round(float(df_valid['dpi_estimate'].mean()), 1)
        if 'contrast_ratio' in df_valid.columns:
            report['avg_contrast'] = round(float(df_valid['contrast_ratio'].mean()), 1)
        
        # Color vs B&W
        if 'is_color' in df_valid.columns:
            report['color_vs_bw'] = df_valid['is_color'].value_counts().to_dict()
        
        # Generate recommendations
        grade_counts = report['omr_grade_distribution']
        total = sum(grade_counts.values())
        
        a_b_percent = (grade_counts.get('A', 0) + grade_counts.get('B', 0)) / total * 100
        
        if a_b_percent >= 70:
            report['recommendations'].append("Excellent: 70%+ of samples are OMR-ready (Grade A/B)")
            report['recommendations'].append("Proceed with automated OMR processing for bulk of archive")
        elif a_b_percent >= 50:
            report['recommendations'].append("Good: 50-70% of samples are OMR-ready")
            report['recommendations'].append("Use OMR for high-quality files, manual transcription for others")
        else:
            report['recommendations'].append("Challenging: <50% of samples are OMR-ready")
            report['recommendations'].append("Consider re-scanning low-quality originals if possible")
        
        if report['avg_dpi'] < 200:
            report['recommendations'].append(f"Average DPI ({report['avg_dpi']}) is below optimal (300)")
            report['recommendations'].append("Preprocessing (upscaling, sharpening) may improve OMR results")
    
    return report

def main():
    """Main analysis process."""
    print("\n" + "="*60)
    print("EMANUEL VOGT ARCHIVE - PHASE 2: ENHANCED QUALITY ANALYSIS")
    print("="*60)
    
    # Step 1: Detailed image analysis
    print("\n📊 Step 1: Analyzing sample images in detail...")
    df_analysis = analyze_sample_set(sample_size=15)
    
    if df_analysis is None:
        return
    
    # Save detailed analysis
    analysis_file = OUTPUT_DIR / "detailed_image_analysis.csv"
    df_analysis.to_csv(analysis_file, index=False)
    print(f"\n✅ Saved detailed analysis: {analysis_file}")
    
    # Step 2: Generate report
    print(f"\n{'='*60}")
    print("📊 Step 2: Generating OMR Readiness Report")
    print(f"{'='*60}")
    
    report = generate_detailed_report(df_analysis)
    
    report_file = OUTPUT_DIR / "omr_readiness_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ Saved report: {report_file}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("OMR READINESS SUMMARY")
    print(f"{'='*60}")
    print(f"Files analyzed: {report['total_analyzed']}")
    print(f"\n📊 OMR Grade Distribution:")
    for grade in ['A', 'B', 'C', 'D']:
        count = report['omr_grade_distribution'].get(grade, 0)
        if count > 0:
            pct = count / report['total_analyzed'] * 100
            print(f"  Grade {grade}: {count} files ({pct:.1f}%)")
    
    print(f"\n📏 Quality Metrics:")
    print(f"  Average DPI: {report['avg_dpi']}")
    print(f"  Average Contrast: {report['avg_contrast']}")
    
    print(f"\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("1. Review detailed_image_analysis.csv for individual file grades")
    print("2. Test a few Grade A files with actual OMR software (Audiveris/MuseScore)")
    print("3. Test a few Grade C/D files to confirm they need manual work")
    print("4. Based on results, decide on processing strategy for full archive")
    print("5. Consider re-scanning low-quality originals if available")

if __name__ == "__main__":
    main()
