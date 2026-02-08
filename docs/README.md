# Emanuel Vogt Archive Project

This repository contains tools and documentation for cataloging, assessing, and publishing the archive of over 2,000 unpublished musical works by composer Emanuel Vogt.

## 📊 Archive Overview

- **Total Files**: 2,341 digital files (2,208 PDFs, 132 JPGs, 1 PNG)
- **Total Size**: ~3.2 GB
- **Works Cataloged**: 1,849 unique work numbers
- **Categories**: 
  - Werke (General Works): 2,084 files
  - Psalmen (Psalms): 257 files
- **Time Span**: 1943 - present

## 📁 Repository Structure

```
emanuelvogt/
├── archive/                    # Main archive (gitignored - files not in repo)
│   ├── files/
│   │   ├── Werke - außer Psalmen/
│   │   └── Psalmen/
│   └── notes/
├── data/                       # Generated data and analysis
│   ├── file_inventory.csv
│   ├── consolidation_summary.json
│   └── quality_assessment/
├── scripts/                    # Python scripts for processing
│   ├── 01_consolidate_catalogs.py
│   └── 02_quality_assessment.py
├── venv/                       # Python virtual environment
├── ARCHIVE_ASSESSMENT_PLAN.md  # Comprehensive planning document
└── README.md                   # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.14+
- Virtual environment (included)

### Setup

1. Clone this repository
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

### Running the Scripts

#### Step 1: Consolidate Catalogs

This script reads all Excel catalogs and creates a unified file inventory:

```bash
python scripts/01_consolidate_catalogs.py
```

**Output:**
- `data/file_inventory.csv` - Complete inventory of all archive files
- `data/*_*.csv` - Individual Excel sheets exported as CSV
- `data/consolidation_summary.json` - Summary statistics

#### Step 2: Quality Assessment

This script analyzes PDF quality and selects representative samples for OMR testing:

```bash
python scripts/02_quality_assessment.py
```

**Output:**
- `data/quality_assessment/sample_files.csv` - 50 representative samples
- `data/quality_assessment/pdf_quality_assessment.csv` - PDF metadata analysis
- `data/quality_assessment/quality_report.json` - Quality summary

## 📋 Current Status

### ✅ Completed

**Phase 1: Archive Assessment** (Feb 4, 2026)
- [x] Archive structure analysis
- [x] File inventory creation (2,341 files cataloged)
- [x] Excel catalog consolidation (4 catalogs processed)
- [x] Representative sampling (50 files selected)
- [x] PDF metadata extraction
- [x] Comprehensive planning document

**Phase 2: Quality Assessment & OMR Readiness** (Feb 5, 2026)
- [x] Enhanced image quality analysis (15 samples)
- [x] DPI and contrast measurement
- [x] OMR readiness prediction
- [x] PDF structure analysis
- [x] **Result: 86.7% of samples are OMR-ready (Grades A+B)!** 🎉

### 🔄 In Progress

**Phase 3: OMR Testing** (Feb 5, 2026)
- [x] OMR software setup (Audiveris & MuseScore)
- [x] Testing pipeline creation (Adaptive scaling script)
- [x] Batch testing of 7 candidate files
- [x] **Result**: 57% success rate with fully automated pipeline. Identified need for "Split Page" strategy for dense scores.

### 🔄 In Progress

**Phase 4: Production Pipeline & Database** (Next)
- [ ] Develop "Split Page" script for high-res files
- [ ] run automated pass on larger batch (e.g. 50 files)
- [ ] Design database schema for tracking conversion status

### 📅 Next Steps

1.  **Verify Results**: User to open `.mxl` files in MuseScore.
2.  **Database Setup**: Initialize SQLite/PostgreSQL database to track 2,300+ files.
3.  **Scale Up**: Run OMR on "Werke 1-100" as a pilot batch.

## 📖 Documentation

See [`ARCHIVE_ASSESSMENT_PLAN.md`](./ARCHIVE_ASSESSMENT_PLAN.md) for:
- Detailed archival situation assessment
- Quality assessment strategy
- Database design recommendations
- Publishing strategy (5 monetization models)
- Phased release plan
- Risk assessment

## 🔧 Technical Details

### File Naming Convention

Works follow this pattern:
```
[Work Number] - [Title] - [Additional Info].[ext]
```

Examples:
- `528 - Improperion.pdf`
- `1 - Sonate für Blockflöte und Gitarre - Seite 1.pdf`

### Work Numbering

- **Werke 1-1711+**: Main compositional works
- **Frühe Werke**: Early works from 1943 onwards
- **Psalmen**: Separate psalm collection
- **Special collections**: e.g., "Werke 2022-2027 aus der Sammlung Grillenberger"

### Quality Metrics

PDFs are assessed on:
- Page count
- Resolution (DPI)
- Encryption status
- OMR readiness
- File size

## 🎯 Project Goals

1. **Archival Assessment**: Create uniform database with unique IDs
2. **Quality Assessment**: Determine machine readability for music generation
3. **Publishing Strategy**: Make archive available and potentially monetizable

## 📊 Key Statistics

From initial analysis:
- Average PDF page count: 1.5 pages
- Page count range: 1-5 pages
- No encrypted PDFs found
- Average file size: 2.08 MB
- 0 processing errors in sample set

## 🤝 Contributing

This is a private archive project. For questions or collaboration inquiries, please contact the repository owner.

## 📄 License

The musical works are protected by copyright. See Schenkungsvertrag documentation for terms.

---

**Last Updated**: February 4, 2026
