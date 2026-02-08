# Emanuel Vogt Archive Assessment & Planning Document

## Executive Summary

The Emanuel Vogt archive contains **2,507 digital files** representing over 2,000 unpublished musical works spanning from 1943 to recent years. This document provides a comprehensive assessment of the current archival situation and proposes strategies for cataloging, quality assessment, and publication.

### Key Findings

- **Total Files**: 2,507 (2,211 PDFs, 295 JPGs, 1 PNG)
- **Organization**: Systematic folder structure with works numbered 1-1796+, plus Psalmen collection and early works
- **Existing Catalogs**: 4 Excel spreadsheets with work listings and GEMA registration data
- **Documentation**: Contract documents, work catalog PDFs, and composer's notes available

---

## 1. Current Archival Situation

### 1.1 Archive Structure

The archive is organized in a hierarchical structure:

```
archive/
├── files/
│   ├── Psalmen/                          (~257 files)
│   │   ├── Die Noten/
│   │   ├── Windsbacher Psalmen - Gesamtausgabe/
│   │   └── Excel catalogs
│   ├── Werke - außer Psalmen/            (~2,250 files)
│   │   ├── Frühe Werke - ab 1943/
│   │   ├── Werke 1 bis 20/
│   │   ├── Werke 21 bis 40/
│   │   ├── ... (systematic 20-work groupings)
│   │   └── Werke 1681 - 1711/
│   └── Excel catalogs
└── notes/
    ├── Werkverzeichnis (work catalog)
    ├── Schenkungsvertrag (donation contract)
    └── Composer's notes
```

### 1.2 Existing Catalog Systems

Four Excel files provide partial cataloging:

1. **2026-01-06 Liste kompositorisches Werk - Endfassung.xlsx** - Main work catalog
2. **2025-11-04 GEMA-Liste Emanuel Vogt.xlsx** - GEMA registration list
3. **Werke_03-11-2025.xlsx** - Alternative work listing
4. **Psalmenaufstellung.xlsx** - Psalm works catalog

### 1.3 File Naming Conventions

Files follow descriptive naming patterns:
- **Format**: `[Work Number] - [Title] - [Additional Info].pdf`
- **Example**: `528 - Improperion.pdf`
- **Multi-page works**: `1 - Sonate für Blockflöte und Gitarre - Seite 1.pdf`

### 1.4 Strengths of Current System

✅ **Systematic numbering** - Works are numbered sequentially  
✅ **Logical grouping** - Organized in batches of 20 works  
✅ **Descriptive titles** - File names include work titles  
✅ **Existing metadata** - Excel catalogs provide additional information  
✅ **Separation by category** - Psalmen vs. other works

### 1.5 Gaps & Challenges

⚠️ **Inconsistent file formats** - Mix of PDF and JPG with varying quality  
⚠️ **No unified database** - Multiple Excel files, potential duplicates/inconsistencies  
⚠️ **Unknown machine readability** - Quality assessment needed for OCR/MusicXML conversion  
⚠️ **Missing metadata** - Composition dates, instrumentation, duration not systematically captured  
⚠️ **No version control** - Multiple scans of same work may exist without clear versioning  
⚠️ **Incomplete coverage** - Not all numbered works may have corresponding files

---

## 2. Quality Assessment Strategy

### 2.1 File Quality Dimensions

To assess suitability for machine reading and music generation, evaluate:

#### A. **PDF Quality Metrics**
- **Resolution**: DPI of scanned images
- **Text layer**: Born-digital vs. scanned PDFs
- **OCR readiness**: Clarity of text elements
- **Music notation clarity**: Staff lines, note heads, symbols
- **Color vs. B&W**: Impact on file size and processing
- **Multi-page handling**: Single vs. multi-page documents

#### B. **JPG Quality Metrics**
- **Resolution**: Pixel dimensions and DPI
- **Compression artifacts**: JPEG quality level
- **Contrast**: Readability of notation
- **Completeness**: Full pages vs. cropped sections

#### C. **Machine Readability Assessment**
- **OMR (Optical Music Recognition) potential**: Can software like Audiveris, PhotoScore read it?
- **OCR potential**: Can text (titles, lyrics, tempo markings) be extracted?
- **Manual transcription need**: Works requiring human intervention

### 2.2 Proposed Sampling Strategy

**Phase 1: Representative Sampling**
1. Select 50 works across different periods:
   - 10 from early works (1943-1960)
   - 10 from Werke 1-400
   - 10 from Werke 401-800
   - 10 from Werke 801-1200
   - 10 from Werke 1201-1711
2. Include both PDF and JPG samples
3. Test with OMR software (Audiveris, MuseScore import)
4. Document quality scores (1-5 scale)

**Phase 2: Systematic Quality Tagging**
- Create quality classification system:
  - **Grade A**: High-resolution, OMR-ready
  - **Grade B**: Good quality, may need preprocessing
  - **Grade C**: Readable, manual transcription likely needed
  - **Grade D**: Poor quality, re-scanning recommended

**Phase 3: Automated Analysis**
- Develop scripts to extract PDF metadata (resolution, page count)
- Batch analyze image quality metrics
- Generate quality report by work number range

### 2.3 Tools & Technologies

| Purpose | Tool Options |
|---------|-------------|
| OMR Testing | Audiveris, PhotoScore, MuseScore, SmartScore |
| PDF Analysis | PyPDF2, pdfinfo, ImageMagick |
| Image Quality | OpenCV, Pillow (Python) |
| OCR | Tesseract, Adobe Acrobat |
| Batch Processing | Python scripts, shell scripts |

---

## 3. Database Design & Cataloging

### 3.1 Proposed Database Schema

#### **Core Tables**

**Works Table**
```
work_id (PK)          - Unique identifier (e.g., EV-0001)
vogt_number           - Original Vogt numbering (1-1711+)
title                 - Work title
subtitle              - Subtitle/alternative title
category              - Psalm, Choral, Instrumental, etc.
composition_date      - Date or year of composition
composition_period    - Early (1943-1960), Middle, Late
instrumentation       - Scoring (SATB, organ, etc.)
duration_minutes      - Approximate duration
text_source           - Biblical, hymn, original, etc.
language              - German, Latin, etc.
dedication            - Dedicatee if any
premiere_date         - First performance date
premiere_location     - Venue/city
publication_status    - Unpublished, Strube, Self-published
gema_registered       - Boolean
gema_number           - GEMA registration number
notes                 - Free-text notes
created_at            - Database record creation
updated_at            - Last modification
```

**Files Table**
```
file_id (PK)
work_id (FK)          - Links to Works table
file_path             - Relative path in archive
file_type             - PDF, JPG, PNG
file_size_bytes       - File size
page_count            - Number of pages
quality_grade         - A, B, C, D
resolution_dpi        - Scan resolution
is_primary            - Boolean (main version)
scan_date             - When scanned
scanner_notes         - Technical notes
ocr_status            - Not attempted, Success, Failed
omr_status            - Not attempted, Success, Failed
musicxml_available    - Boolean
created_at
```

**Metadata Table** (flexible key-value for additional data)
```
metadata_id (PK)
work_id (FK)
key                   - Metadata field name
value                 - Metadata value
```

### 3.2 Unique ID System

**Proposed Format**: `EV-[CATEGORY]-[NUMBER]`

Examples:
- `EV-PS-001` - Psalm work #1
- `EV-CH-0523` - Choral work #523
- `EV-IN-0042` - Instrumental work #42
- `EV-EW-1943-01` - Early work from 1943, #1

**Alternative**: Keep Vogt's original numbering as primary, add UUID for database integrity
- `vogt_number`: 528
- `uuid`: `550e8400-e29b-41d4-a716-446655440000`

### 3.3 Integration with Existing Excel Catalogs

**Migration Strategy**:
1. Parse existing Excel files
2. Map columns to database schema
3. Resolve conflicts between different catalogs
4. Import data with validation
5. Flag records needing manual review
6. Keep Excel files as historical reference

### 3.4 Technology Stack Options

| Approach | Technology | Pros | Cons |
|----------|-----------|------|------|
| **Relational DB** | PostgreSQL + Python | Robust, queryable, scalable | Requires setup |
| **Document DB** | MongoDB | Flexible schema | Less structured |
| **Spreadsheet+** | Airtable, Notion | User-friendly, no coding | Limited customization |
| **Static Site** | SQLite + Static Generator | Portable, version-controllable | Less dynamic |

**Recommendation**: PostgreSQL with Python (Django/Flask) for robust long-term solution, or Airtable for quick MVP.

---

## 4. Publishing Strategy

### 4.1 Target Audiences

1. **Academic Researchers** - Musicologists, composition students
2. **Performers** - Choirs, organists, chamber ensembles
3. **Music Publishers** - Potential commercial partners
4. **General Public** - Classical music enthusiasts
5. **Libraries & Archives** - Institutional collections

### 4.2 Publication Platforms

#### **Digital Archive Platforms**

| Platform | Type | Features | Cost Model |
|----------|------|----------|------------|
| **IMSLP** | Free sheet music library | Massive reach, public domain focus | Free (donations) |
| **CPDL** | Choral public domain library | Choral-specific community | Free |
| **Issuu** | Digital publishing | Beautiful presentation | Freemium |
| **Archive.org** | Digital preservation | Permanent archiving | Free |
| **Custom Website** | Self-hosted | Full control | Development cost |

#### **Commercial Platforms**

| Platform | Type | Revenue Model |
|----------|------|---------------|
| **Musicaneo** | Self-publishing for composers | Commission on sales |
| **SheetMusicPlus** | Major retailer | Wholesale pricing |
| **JW Pepper** | Educational music | Wholesale/consignment |
| **Strube Verlag** | Existing relationship | Traditional publishing |

#### **Streaming & Performance**

| Platform | Type | Purpose |
|----------|------|---------|
| **YouTube** | Video | Recordings, score videos |
| **SoundCloud** | Audio | Sample recordings |
| **Spotify/Apple Music** | Streaming | Commercial recordings |
| **MuseScore.com** | Interactive scores | Playback, sharing |

### 4.3 Monetization Models

#### **Model 1: Freemium**
- ✅ Low-resolution PDFs free on IMSLP/CPDL
- 💰 High-resolution, print-quality PDFs for purchase
- 💰 Performance parts (separate from score) for purchase
- 💰 MusicXML/Sibelius files for purchase

#### **Model 2: Subscription**
- 💰 Monthly/annual access to full catalog
- ✅ Free preview of 10-20 representative works
- 💰 Institutional licenses for universities

#### **Model 3: Traditional Publishing**
- Partner with Strube Verlag or similar
- Select "best" 50-100 works for print publication
- Remainder available digitally
- Revenue sharing agreement

#### **Model 4: Hybrid Open Access**
- ✅ All works freely available after 2-year embargo
- 💰 Early access for supporters
- 💰 Premium features (transpositions, parts, MusicXML)
- 💰 Commissioned recordings

#### **Model 5: Patronage/Crowdfunding**
- Kickstarter/Patreon for digitization costs
- Supporters get early access, credits
- Gradual release as funding goals met
- Community involvement in selection

### 4.4 Copyright & Licensing Considerations

> **IMPORTANT**: Emanuel Vogt's works are protected by copyright. Clarify:
> - Who holds copyright? (Composer, heirs, foundation?)
> - What are the terms of the donation/Schenkungsvertrag?
> - Can works be released under Creative Commons?

**Licensing Options**:
- **All Rights Reserved** - Traditional copyright, maximum control
- **CC BY-NC-ND** - Attribution, non-commercial, no derivatives
- **CC BY-NC-SA** - Attribution, non-commercial, share-alike (allows arrangements)
- **CC BY** - Attribution only (most open)

**GEMA Considerations**: Some works already registered with GEMA. Coordinate licensing with existing registrations.

### 4.5 Phased Release Strategy

#### **Phase 1: Foundation (Months 1-3)**
- Complete database of all works
- Quality assessment of full catalog
- Select 50 "showcase" works (highest quality, representative)
- Create website/platform
- Digitize showcase works to MusicXML if needed

#### **Phase 2: Soft Launch (Months 4-6)**
- Release showcase works publicly (free or freemium)
- Gather feedback from performers/researchers
- Build email list/community
- Test monetization model
- Secure partnerships (publishers, performers)

#### **Phase 3: Systematic Release (Months 7-18)**
- Release works in thematic batches:
  - Psalmen collection
  - Choral works by liturgical season
  - Instrumental works by ensemble type
- Monthly or quarterly releases maintain interest
- Commission recordings of selected works
- Academic partnerships (dissertations, performances)

#### **Phase 4: Complete Archive (Months 19-24)**
- Full catalog available
- Advanced search and filtering
- User-contributed recordings/performances
- Educational resources (analysis, performance notes)
- Sustainability plan (ongoing maintenance)

### 4.6 Marketing & Outreach

**Target Channels**:
- **Academic**: Music journals, conference presentations, university libraries
- **Performers**: Choral directors associations, organist guilds, chamber music networks
- **Digital**: Social media (YouTube, Instagram), music blogs, podcasts
- **Traditional**: Press releases, concert program notes, radio features

**Content Marketing**:
- "Work of the Week" blog posts
- Score analysis videos
- Composer biography series
- Performance guides
- Historical context articles

### 4.7 Technical Infrastructure

**Minimum Viable Platform**:
```
Website Components:
├── Homepage - Composer bio, project overview
├── Catalog Browser - Searchable/filterable work list
├── Work Detail Pages - Score preview, metadata, download
├── About/Documentation - Project background, usage terms
└── Contact/Support - Inquiries, feedback
```

**Technology Stack**:
- **Static Site**: Hugo/Jekyll + GitHub Pages (free, fast)
- **Dynamic Site**: WordPress + WooCommerce (e-commerce ready)
- **Custom App**: Django/Flask + PostgreSQL (full control)
- **Hybrid**: Airtable database + Webflow/Squarespace frontend

**File Hosting**:
- **Small-scale**: GitHub LFS, Dropbox, Google Drive
- **Medium-scale**: AWS S3, Backblaze B2
- **Large-scale**: CDN (Cloudflare, Fastly)

---

## 5. Immediate Next Steps

### 5.1 Critical Questions for Stakeholders

> **Decision Required**: The following questions must be answered before proceeding:

1. **Copyright & Permissions**
   - Who legally controls the works?
   - What are the terms of the Schenkungsvertrag?
   - Are there restrictions on digital distribution?

2. **Budget & Resources**
   - What funding is available for digitization?
   - Is there budget for OMR software, hosting, development?
   - Are volunteers/interns available for data entry?

3. **Timeline & Priorities**
   - What is the target launch date?
   - Which works should be prioritized?
   - Is there a deadline (anniversary, event)?

4. **Monetization Goals**
   - Is revenue generation essential or secondary?
   - What is the acceptable balance between access and income?
   - Are there donors/sponsors to support free access?

### 5.2 Recommended Action Plan

#### **Week 1-2: Data Consolidation**
1. Export all Excel catalogs to CSV
2. Cross-reference work numbers across catalogs
3. Identify gaps and duplicates
4. Create master spreadsheet with all known metadata

#### **Week 3-4: Quality Sampling**
1. Select 50 representative works
2. Test OMR software on samples
3. Document quality grades
4. Estimate percentage of OMR-ready works

#### **Week 5-6: Database Design**
1. Finalize database schema
2. Choose technology stack
3. Set up development environment
4. Create data import scripts

#### **Week 7-8: Legal & Business**
1. Review Schenkungsvertrag with legal counsel
2. Decide on licensing model
3. Draft terms of use
4. Research partnership opportunities

#### **Week 9-12: MVP Development**
1. Build basic catalog website
2. Import metadata to database
3. Upload showcase works
4. Test with small user group

### 5.3 Success Metrics

**Short-term (6 months)**:
- Complete database of all 2000+ works
- Quality assessment of 100% of files
- 50 works available online
- 500 website visitors
- 5 partnerships (performers, institutions)

**Medium-term (12 months)**:
- 500+ works available
- 5,000 website visitors
- 100 downloads/month
- 10 performances of works
- Revenue covering hosting costs (if monetized)

**Long-term (24 months)**:
- Full catalog online
- 20,000+ website visitors
- 500+ downloads/month
- 50+ performances annually
- Academic citations/research
- Sustainable funding model

---

## 6. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Copyright disputes** | High | Low | Legal review of Schenkungsvertrag |
| **Low file quality** | Medium | Medium | Budget for re-scanning if needed |
| **No audience interest** | Medium | Low | Market research, soft launch testing |
| **Technical failures** | Medium | Low | Backups, version control, staging environment |
| **Insufficient funding** | High | Medium | Phased approach, crowdfunding, grants |
| **Incomplete metadata** | Low | High | Accept gaps, improve iteratively |
| **Platform obsolescence** | Medium | Low | Use open standards (PDF, MusicXML) |

---

## 7. Conclusion

The Emanuel Vogt archive represents a significant cultural asset with **2,507 files** documenting a prolific composer's life work. The systematic organization and existing catalogs provide a strong foundation, but quality assessment and unified database creation are essential next steps.

**Key Recommendations**:

1. **Prioritize database creation** - Consolidate existing Excel catalogs into robust system
2. **Conduct quality assessment** - Sample-based testing to determine OMR readiness
3. **Clarify legal framework** - Review copyright and licensing before publication
4. **Adopt phased release** - Start with showcase works, expand systematically
5. **Choose hybrid monetization** - Balance accessibility with sustainability
6. **Build community** - Engage performers, researchers, and enthusiasts early

With proper planning and execution, this archive can become a valuable resource for musicians worldwide while honoring Emanuel Vogt's legacy.

---

## Appendices

### A. Folder Structure Summary

**Werke - außer Psalmen**: ~103 folders organized as:
- Frühe Werke - ab 1943 (early works)
- Werke 1 bis 20, 21 bis 40, ... (systematic 20-work batches)
- Werke 1001-1020, 1021-1040, ... (continuation into 4-digit numbers)
- Highest observed: Werke 1681-1711
- Special: "Werke 2022-2027 aus der Sammlung Grillenberger"

**Psalmen**: Separate collection with ~257 files including:
- Individual psalm settings
- Windsbacher Psalmen collection (published by Strube)
- Academic thesis on the Windsbacher Psalmen

### B. File Format Breakdown

- **PDF files**: 2,211 (88.2%)
- **JPG files**: 295 (11.8%)
- **PNG files**: 1 (0.04%)

### C. Existing Documentation Files

Located in `archive/notes/`:
- Werkverzeichnis Emanuel Vogt 2025.pdf - Work catalog
- Gedanken zu meiner Arbeit.pdf - Composer's thoughts
- Schenkungsvertrag documents - Donation contracts
- Correspondence with journals/newspapers

### D. Resources for Further Research

**OMR Software**:
- Audiveris (open-source): https://audiveris.github.io/
- MuseScore (import): https://musescore.org/
- PhotoScore: https://www.avid.com/sibelius/photoscore
- SmartScore: https://www.musitek.com/

**Digital Music Archives**:
- IMSLP: https://imslp.org/
- CPDL: https://www.cpdl.org/
- RISM: https://rism.info/

**Music Publishing Platforms**:
- Musicaneo: https://www.musicaneo.com/
- Sheet Music Plus: https://www.sheetmusicplus.com/
- JW Pepper: https://www.jwpepper.com/
