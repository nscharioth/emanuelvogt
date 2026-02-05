# Phase 3: OMR Testing Instructions

**Status**: Ready for Testing
**Date**: February 5, 2026

We have identified 7 "Grade A" files that are excellent candidates for Optical Music Recognition (OMR). These files have been copied to `data/omr_testing/candidates/`.

## 🛠️ Step 1: Install OMR Software

We need a dedicated OMR engine. **Audiveris** is suitable for this.

### Option A: Audiveris (Recommended)
1.  **Download** the latest DMG for macOS from the official releases:
    [https://github.com/Audiveris/audiveris/releases](https://github.com/Audiveris/audiveris/releases)
    *(Look for `Audiveris-5.x.x-macos.dmg`)*
2.  **Install** it by dragging to Applications.
3.  **Run** it once to ensure it initializes correctly.

### Option B: MuseScore (Already Installed)
We have installed MuseScore 4. You can try opening the candidate PDFs directly in MuseScore:
1.  Open MuseScore 4.
2.  Click **File > Open** (or Import).
3.  Select one of the PDFs from `emanuelvogt/data/omr_testing/candidates/`.
4.  *Note: MuseScore often uses an online service for PDF conversion, which might require an account.*

## 🧪 Step 2: Run the Test

### Manual Test (Best for first check)
1.  Open **Audiveris**.
2.  Drag and drop the files from `data/omr_testing/candidates/` into Audiveris.
3.  Click the **Transcribe** button (book icon).
4.  Check the results:
    *   Are the notes detected correctly?
    *   is the text (lyrics) preserved?
5.  Export as **MusicXML** (.mxl).

### Automated Test
If you have `audiveris` available in your terminal path, you can run our testing script:

```bash
source venv/bin/activate
python scripts/06_run_omr_test.py
```

## 📝 Step 3: Grade the Results

After testing, please create a file `data/omr_testing/results_log.csv` with the following columns:
*   `filename`
*   `success` (Yes/No)
*   `accuracy_rating` (1-5, where 5 is perfect)
*   `notes` (e.g., "Missed lyrics", "Perfect", "Wrong key")

## 📂 Candidate Files
The following files are ready for testing in `data/omr_testing/candidates/`:

1. `48 - Psalm 47 - Seite 1.pdf`
2. `91b - Inmitten der Nacht.pdf`
3. `11 - EG 11 - Wie soll ich dich....pdf`
4. `7 - Psalm 19 - Seite 2.pdf`
5. `191 - Danza Hungaria - Seiten 2 - 5.pdf`
6. `298 - Ohne Titel.pdf`
7. `422 - Fröhliche Weihnacht - Titelseite.pdf`

---
**Next Step**: Once you have graded a few files, we can extrapolate the success rate to the wider archive.
