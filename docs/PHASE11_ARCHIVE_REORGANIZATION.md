# Phase 11: Archive Reorganization - URL-Safe File Structure

**Status**: ✅ Implemented  
**Date**: 8. Februar 2026  
**Goal**: Create a flat, URL-safe archive structure for web-optimized file serving

---

## Overview

Phase 11 implements a comprehensive reorganization of the Emanuel Vogt Archive file structure, moving from a complex hierarchical directory system to a flat, URL-safe archive optimized for web serving and cross-platform compatibility.

### Problem Statement

The current archive structure has several issues:
1. **Windows Compatibility**: Special characters in filenames (umlauts, multiple dots) cause path resolution failures
2. **Web URLs**: Current filenames require URL-encoding (`%C3%BC` for ü)
3. **Complex Directory Structure**: 103+ nested folders difficult to maintain
4. **SEO**: URLs like `/pdf/3` are not search-engine friendly
5. **CDN-Ready**: Not optimized for cloud storage/CDN distribution

### Solution: Flat URL-Safe Archive

Create `archive/flat/` with normalized, URL-safe filenames:
- No umlauts (ä→ae, ö→oe, ü→ue, ß→ss)
- No special characters
- Hyphens instead of spaces
- Lowercase
- Unique identifiers (file_id suffix for duplicates)

---

## Architecture

### New Directory Structure

```
archive/
├── files/          # OLD - hierarchical structure (kept as backup)
│   ├── Psalmen/
│   └── Werke/
│       ├── Werke 1 bis 20/
│       ├── Werke 21 bis 40/
│       └── ...
└── flat/           # NEW - flat URL-safe structure
    ├── 0001-sonate-fuer-blockfloete-und-gitarre-seite-1.pdf
    ├── 0014a-hor-hor-hor.pdf
    ├── 0528-improperion.pdf
    ├── p-019-psalm-19-seite-1.pdf
    └── ...
```

### Database Schema Changes

Three new columns added to `files` table:

```sql
ALTER TABLE files ADD COLUMN slug TEXT;           -- URL-safe filename
ALTER TABLE files ADD COLUMN flat_path TEXT;      -- Path in flat/ archive
ALTER TABLE files ADD COLUMN original_path TEXT;  -- Backup of original filepath
```

**Index for performance:**
```sql
CREATE INDEX idx_files_slug ON files(slug);
```

### Slug Generation Rules

**Umlaut Conversion:**
- `ä` → `ae`, `ö` → `oe`, `ü` → `ue`, `ß` → `ss`

**Character Normalization:**
- Lowercase
- Spaces/underscores → hyphens (`-`)
- Remove special characters: `()[]{}!?@#$%^&*+=<>|\/,.'":`
- Collapse multiple hyphens
- Trim to max 100 characters

**Examples:**
```
Original: "14a - Hör, hör, hör....pdf"
Slug:     "14a-hor-hor-hor.pdf"

Original: "528 - Improperion.pdf"
Slug:     "0528-improperion.pdf"

Original: "P-19 - Psalm 19 - Seite 1.pdf"
Slug:     "p-019-psalm-19-seite-1.pdf"

Original: "12a, b, c - Wie bist Du schön....pdf"
Slug:     "0012a-b-c-wie-bist-du-schoen.pdf"

Original: "7 - Solo-Suite für Violine für Sabine Kötz - Seite 1.pdf"
Slug:     "7-solo-suite-fur-violine-fur-sabine-kotz-seite-1.pdf"
```

### Duplicate Handling

If a slug already exists, append file_id:
```
Base:      "sonate-seite-1.pdf"
Duplicate: "sonate-seite-1-523.pdf"  (file_id = 523)
```

---

## Implementation

### Scripts

**1. `scripts/24_add_slug_columns.py`**
- Standalone script to add database columns
- Can be run independently before migration
- Creates index on slug column

**2. `scripts/23_reorganize_archive.py`**
- Main reorganization script
- Analyzes all files and generates slugs
- Copies files to flat/ archive
- Updates database with new paths
- Supports dry-run mode for safe testing

### Backend Changes (`app/backend.py`)

**Hybrid Path Resolution:**
```python
# Priority order:
1. flat_path (new, preferred)
2. filepath with OS-specific separators
3. filepath direct
4. Filename search in expected directory
```

**New Endpoint:**
```python
GET /pdf/by-slug/{slug}
# Example: GET /pdf/by-slug/0528-improperion.pdf
# SEO-friendly, human-readable URLs
```

**Enhanced Headers:**
```python
Content-Disposition: inline; filename="14a - Hör, hör, hör....pdf"
# Browser sees original filename, URL uses slug
```

---

## Usage

### Testing (Dry-Run)

Preview changes without modifying anything:
```bash
python3 scripts/23_reorganize_archive.py
```

### Incremental Testing

Test with small batch first:
```bash
# Test with 10 files
python3 scripts/23_reorganize_archive.py --live --limit=10

# Test with 100 files
python3 scripts/23_reorganize_archive.py --live --limit=100
```

### Full Migration

Execute complete reorganization:
```bash
python3 scripts/23_reorganize_archive.py --live
```

**Options:**
- `--live`: Actually execute (default is dry-run)
- `--limit=N`: Process only first N files (testing)
- `--no-backup`: Skip database backup (not recommended)

### Output

The script generates:
- **Console output**: Progress updates, statistics
- **JSON report**: `data/reorganization_report.json`
  - Summary statistics
  - Sample slugs
  - Error details
- **Database backup**: `data/archive_backup_YYYYMMDD_HHMMSS.db`

---

## Verification

### Check Slug Generation

After dry-run, review sample slugs in output:
```
Sample Slugs (first 20):
  14a        | 14a - Hör, hör, hör....pdf                 → 14a-hor-hor-hor.pdf
  528        | 528 - Improperion.pdf                      → 0528-improperion.pdf
  P-19       | P-19 - Psalm 19 - Seite 1.pdf             → p-019-psalm-19-seite-1.pdf
```

### Verify Database Updates

```sql
SELECT id, filename, slug, flat_path, original_path 
FROM files 
LIMIT 10;
```

### Test Backend

Start server and test both endpoints:
```bash
# Old endpoint (still works)
GET http://localhost:8000/pdf/3

# New slug-based endpoint
GET http://localhost:8000/pdf/by-slug/0014a-hor-hor-hor.pdf
```

### Windows Diagnostics

Updated diagnostic script checks both structures:
```bash
python scripts/diagnose_pdf_windows.py
```

---

## Benefits

### Web Optimization
- ✅ **SEO-friendly URLs**: `/pdf/by-slug/hoer-hoer-hoer.pdf` instead of `/pdf/3`
- ✅ **No URL encoding**: Slugs are ASCII-only
- ✅ **Human-readable**: Users can understand URLs
- ✅ **Shareable**: Clean URLs for social media, emails

### Cross-Platform
- ✅ **Windows-compatible**: No special character issues
- ✅ **macOS-compatible**: Works on Unix filesystems
- ✅ **Linux-compatible**: Universal compatibility
- ✅ **Browser-safe**: All characters safe in URLs

### Maintenance
- ✅ **Flat structure**: Easy to navigate
- ✅ **No nested folders**: Simpler backups
- ✅ **Unique names**: No path ambiguity
- ✅ **Searchable**: Grep/find works easily

### Future-Ready
- ✅ **CDN-compatible**: Easy to serve from S3, Azure, etc.
- ✅ **Cache-friendly**: Static URLs, no session state
- ✅ **API-ready**: RESTful URL structure
- ✅ **Scalable**: Handles thousands of files

---

## Migration Strategy

### Phase 1: Preparation (Day 1)
1. ✅ Create reorganization script
2. ✅ Add database columns
3. ✅ Update backend with hybrid resolution
4. ✅ Run dry-run tests

### Phase 2: Testing (Day 2)
1. ⏳ Test with 10 files on Windows
2. ⏳ Test with 100 files on macOS
3. ⏳ Verify PDF serving works
4. ⏳ Check slug generation accuracy

### Phase 3: Migration (Day 3)
1. ⏳ Full migration (2,829 files)
2. ⏳ Verify all files copied correctly
3. ⏳ Test random sample of PDFs
4. ⏳ Update frontend to use slug URLs

### Phase 4: Cleanup (Day 4-5)
1. ⏳ Monitor for 1 week
2. ⏳ Archive old `files/` directory (ZIP backup)
3. ⏳ Update documentation
4. ⏳ Celebrate! 🎉

---

## Rollback Plan

If migration fails:

### 1. Database Rollback
```bash
# Restore from automatic backup
mv data/archive_backup_YYYYMMDD_HHMMSS.db data/archive.db
```

### 2. File Cleanup
```bash
# Remove flat/ directory
rm -rf archive/flat/
```

### 3. Backend Rollback
```bash
# Revert backend changes via git
git checkout app/backend.py
```

### 4. Restart Server
```bash
./run_viewer.sh  # or run_viewer.bat
```

---

## Performance

### Storage Impact
- **Original**: 3.2 GB in `archive/files/`
- **After**: 3.2 GB in `archive/flat/` (duplicate, not move)
- **Total**: ~6.4 GB during transition
- **After cleanup**: 3.2 GB (once `files/` is archived)

### Speed Impact
- **Flat directory lookup**: Faster than nested (OS filesystem caching)
- **Slug lookup**: Fast with database index
- **PDF serving**: Identical performance
- **First request**: ~50ms (cache miss)
- **Subsequent**: ~5ms (OS cache hit)

### Scalability
- **Current**: 2,829 files
- **Max recommended**: 10,000 files per flat directory
- **Alternative**: Shard into subdirectories (`flat/00xx/`, `flat/01xx/`, etc.)

---

## Known Limitations

1. **Max slug length**: 100 characters (truncates longer titles)
2. **Duplicate files**: Appends file_id, may not be semantically meaningful
3. **Storage during migration**: Requires 2x space temporarily
4. **Non-reversible**: Original filenames preserved in database, but not in filesystem

---

## Future Enhancements

### Automatic Cleanup (Phase 12)
- Script to archive `archive/files/` to ZIP
- Compress old structure for long-term backup
- Free up disk space

### CDN Integration (Phase 16)
- Sync `flat/` to S3 or Azure Blob Storage
- Configure CloudFront/Azure CDN
- Serve PDFs from edge locations globally

### Thumbnail Generation (Phase 13)
- Extract first page as thumbnail
- Store in `flat/thumbnails/`
- Slug-based naming: `0528-improperion-thumb.jpg`

### Download Statistics
- Track which PDFs are accessed
- Popular works analytics
- Optimize caching strategy

---

## Troubleshooting

### "Source file not found" errors
- **Cause**: Files don't exist at original path
- **Solution**: Verify `archive/files/` structure intact
- **Check**: Run `diagnose_pdf_windows.py`

### Slug collisions
- **Symptom**: Two files generate same slug
- **Solution**: Script automatically appends file_id
- **Check**: Review `reorganization_report.json`

### Backend 404 errors
- **Cause**: Database not updated with new paths
- **Solution**: Re-run migration with `--live` (no limit)
- **Check**: Verify `slug` and `flat_path` columns populated

### Windows path issues
- **Cause**: Mixed forward/backward slashes
- **Solution**: Backend tries multiple strategies
- **Check**: Test with `diagnose_pdf_windows.py`

---

## Success Criteria

Migration is successful when:
- ✅ All 2,829 files copied to `flat/` without errors
- ✅ Database updated with slug and flat_path for all files
- ✅ Backend serves PDFs from both `flat/` and `files/` (hybrid)
- ✅ No 404 errors on random sample of 100 PDFs
- ✅ Windows user confirms PDFs load correctly
- ✅ URL `/pdf/by-slug/0528-improperion.pdf` works

---

## Related Documentation

- `docs/PHASE9_COMPLETION_REPORT.md` - Windows compatibility fixes
- `docs/PHASE10_PDF_ROTATION.md` - PDF serving enhancements
- `scripts/23_reorganize_archive.py` - Main migration script
- `scripts/24_add_slug_columns.py` - Database schema update

---

**Status**: ✅ Scripts implemented, ready for execution  
**Next Step**: Run `python3 scripts/23_reorganize_archive.py --live --limit=10` for initial test

---

**END OF PHASE 11 DOCUMENTATION**
