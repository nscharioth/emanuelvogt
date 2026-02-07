# Windows Compatibility Fix

**Date**: 7. Februar 2026  
**Issue**: Directory names with special characters cause access problems on Windows

---

## Problem

The directory name `Werke - außer Psalmen` contains:
- Em-dash/hyphen with spaces
- Umlaut (ä) character

This causes issues on Windows systems:
- File access errors
- Path encoding problems
- PDF viewer loading failures

---

## Solution

### Automated Migration Script

Run the migration script to fix the directory structure:

```bash
# macOS/Linux
python scripts/11_fix_directory_names.py

# Windows
python scripts\11_fix_directory_names.py
```

### What the Script Does

1. **Creates Database Backup**
   - Saves `archive_backup_before_rename.db`
   - Ensures rollback capability

2. **Renames Directory**
   - From: `Werke - außer Psalmen`
   - To: `Werke`

3. **Updates Database Paths**
   - Updates all `files.filepath` entries
   - Uses SQL `REPLACE` function
   - Commits only if successful

4. **Verifies Changes**
   - Checks sample files exist
   - Confirms no old paths remain

---

## Manual Alternative

If the script fails, you can perform the migration manually:

### Step 1: Rename Directory

```bash
# In terminal (macOS/Linux)
cd archive/files
mv "Werke - außer Psalmen" Werke

# Windows Command Prompt
cd archive\files
ren "Werke - außer Psalmen" Werke
```

### Step 2: Update Database

```sql
-- Connect to SQLite database
sqlite3 data/archive.db

-- Update file paths
UPDATE files 
SET filepath = REPLACE(filepath, 'Werke - außer Psalmen', 'Werke')
WHERE filepath LIKE '%Werke - außer Psalmen%';

-- Verify
SELECT COUNT(*) FROM files WHERE filepath LIKE '%Werke - außer Psalmen%';
-- Should return: 0

-- Exit
.quit
```

---

## Impact

### Before Fix
- **Total Files Affected**: ~2,000 PDF files
- **Problem**: Windows cannot access PDFs in "Werke - außer Psalmen"
- **Status**: ❌ Cross-platform incompatible

### After Fix
- **Directory Name**: `Werke` (simple, no special characters)
- **Database Paths**: Updated automatically
- **Status**: ✅ Windows/macOS/Linux compatible

---

## Testing Checklist

After migration, verify:

- [ ] Web interface loads correctly
- [ ] PDFs open in viewer (both Psalmen and Werke)
- [ ] Search function works
- [ ] All file counts match (2,829 files)
- [ ] No 404 errors on Windows systems

---

## Rollback Procedure

If problems occur after migration:

1. **Restore Database Backup**:
   ```bash
   cp data/archive_backup_before_rename.db data/archive.db
   ```

2. **Rename Directory Back**:
   ```bash
   cd archive/files
   mv Werke "Werke - außer Psalmen"
   ```

---

## Additional Encoding Improvements

For future-proofing, consider:

1. **URL Encoding in Backend**
   - Use `urllib.parse.quote()` for file paths in URLs
   - Already partially implemented in FastAPI

2. **Filename Normalization**
   - Remove or replace special characters in filenames
   - Use slugify for new uploads

3. **Database Encoding Settings**
   - SQLite already uses UTF-8
   - Text factory handles encoding errors gracefully

---

## Related Files

- **Migration Script**: `scripts/11_fix_directory_names.py`
- **Database Schema**: `scripts/07_init_database.py`
- **Backend API**: `app/backend.py`
- **Backup Location**: `data/archive_backup_before_rename.db`

---

## Status

- [ ] Migration script created
- [ ] Database backup created
- [ ] Directory renamed
- [ ] Database paths updated
- [ ] Verification passed
- [ ] Windows testing completed

**Recommendation**: Run migration script during off-hours to avoid disrupting active users.
