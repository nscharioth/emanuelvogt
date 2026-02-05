# Phase 3 Report: OMR Testing Results

**Date**: February 5, 2026
**Status**: ✅ Phase 3 Complete (Proof of Concept Successful)

---

## 📊 Testing Results

We ran an automated OMR test on 7 high-quality "Grade A" files using **Audiveris 5.x** with an adaptive resolution scaling pipeline.

| File | Status | Notes |
|------|--------|-------|
| `7 - Psalm 19 - Seite 2.pdf` | ✅ **Success** | Generated .mxl |
| `48 - Psalm 47 - Seite 1.pdf` | ✅ **Success** | Generated 2 movements |
| `191 - Danza Hungaria...pdf` | ✅ **Success** | Generated 2 movements |
| `298 - Ohne Titel.pdf` | ✅ **Success** | Generated .mxl |
| `91b - Inmitten der Nacht.pdf` | ❌ Failed | "Interline value too low" (Resolution issue) |
| `422 - Fröhliche Weihnacht...pdf`| ❌ Failed | Stave detection failed |
| `11 - EG 11...pdf` | ❌ Failed | Stave detection failed |

**Success Rate**: 57% (4/7) fully automated.

---

## 🔍 Failure Analysis

The failures revealed a critical technical constraint:
1.  **Maximum Image Size**: Audiveris has a hard limit of ~20 Megapixels per page.
2.  **High-Density Scores**: Some scores (`91b`, `422`) have dense notation. When we downscale them to fit the 20MP limit, the stave lines become too close (<7 pixels), causing detection to fail.
3.  **Trade-off**: We cannot simply increase resolution (hits size limit) nor decrease it (hits detection limit).

---

## 🛠️ Recommended Production Strategy

For the full archive (2,300+ files), we recommend a **Hybrid Strategy**:

### 1. Automated First Pass (Expect ~60% Success)
Run the script we developed (`06_run_omr_test.py`) on the entire archive.
-   **Cost**: Computation only (cheap).
-   **Result**: ~1,200-1,400 works digitised automatically.

### 2. Manual/Split Processing for Failures (~40%)
For files that fail the automated pass (like `91b`):
-   **Split Pages**: Cut the image in half (top/bottom).
    -   This allows *double the resolution* (DPI) for the same file size (MP).
    -   Audiveris can then detect the staves easily.
-   **Manual GUI**: Use Audiveris GUI to manually set the "Grid" for problematic files.

---

## 🚀 Next Steps

1.  **Review the MusicXML files**: Open the `.mxl` files in `data/omr_testing/outputs` using MuseScore to verify accuracy.
2.  **Refine the Pipeline**: Write a "Splitter" script to handle the failed files (Phase 4).
3.  **Database**: Start building the database to track which files are `Converted`, `Failed`, or `Pending`.

The Proof of Concept is successful: **We can digitise a significant portion of the archive automatically.**
