# Strategy Pivot: Beyond Automated OMR

**Date**: February 5, 2026
**Status**: DRAFT for Decision

## 🚨 The Situation
We have confirmed that **automated open-source OMR (Audiveris) is not viable** for this archive.
-   **The Good**: The archive contains 2,341 high-quality PDF scans (~600 DPI).
-   **The Bad**: The musical complexity, density, and handwriting/typesetting require human interpretation. The generated MusicXML files are garbled and unusable.

## 🎯 The Core Question
**Do we strictly need machine-readable files (MusicXML/MIDI) for *every* work?**
-   **Yes**: If the goal is to allow playback, transposition, or editing for everything.
-   **No**: If the goal is to preserve the work and make it accessible to musicians who can read sheet music.

## 🛣️ Strategic Options

### Option 1: The "Digital Library" Approach (Recommended) 🏆
**Goal**: Build a beautiful, searchable website hosting the original PDF facsimiles.
**MusicXML**: Only for a "Best of" selection (e.g., Top 50 works).

-   **Pros**:
    -   **Feasible**: We have the PDFs. We can build this *now*.
    -   **High Quality**: Users see exactly what Emanuel Vogt wrote/approved.
    -   **Professional**: Standard approach for archives (e.g., IMSLP, Bach Digital).
-   **Cons**:
    -   No audio playback for most works.
    -   Users cannot transpose scores.
-   **Workflow**:
    1.  **Database**: Index all 2,341 files (Works 1-1849).
    2.  **Website**: Build a search engine ("Find Psalm 23").
    3.  **Manual Transcription**: Identify the 50 most important works and pay/volunteer to transcribe them properly.

### Option 2: The "Commercial OMR" Approach
**Goal**: Attempt to rescue the automation dream using paid enterprise software.
**Tools**: PhotoScore Ultimate ($250), SmartScore ($400), or ScanScore.

-   **Pros**:
    -   Significantly better accuracy than Audiveris.
    -   Might handle the density issues better.
-   **Cons**:
    -   **Cost**: License fees.
    -   **Risk**: Still requires manual correction (typically 5-15 mins per page). For 2,000 works, that's still 5,000+ hours of work.
    -   Result might still be imperfect.

### Option 3: The "Crowdsourced" Approach
**Goal**: Engage the community to transcribe the archive over time.
**Platform**: Build a "Wiki-style" platform.

-   **Pros**:
    -   Zero cost to us.
    -   Engages the community (choirs, students).
-   **Cons**:
    -   Slow.
    -   Quality control is difficult.
    -   Requires building a complex collaborative platform.

---

## 💡 Recommendation: Pivot to Option 1 (Digital Library)

We should adjust our definition of success. A "perfect MusicXML database" is a multi-year/multi-budget project. A "perfect PDF Archive" is achievable in **4-6 weeks**.

### Revised Roadmap

**Phase 4: Database & Search (Weeks 1-2)**
-   Create a robust SQLite/PostgreSQL database.
-   Ingest all metadata (titles, instrumentation, work numbers).
-   Link PDFs to database records.

**Phase 5: The "Emanuel Vogt Portal" (Weeks 3-4)**
-   Build a web interface (Next.js/React).
-   Features: "Search by Psalm", "Browse by Year", "View PDF".
-   Tagging system for machine readability *of metadata* (not music).

**Phase 6: Selective Digitisation (Ongoing)**
-   Add a "Request Transcription" button to the website.
-   Prioritize works based on user interest.
-   Manually transcribe the top requested works.

---

## 📞 Decision Required

Please confirm if we should **pivot to Option 1 (PDF-First Archive)**.
This allows us to stop fighting the OMR tools and start building a valuable, working product immediately.
