# Database Schema Design
**Project**: Emanuel Vogt Digital Archive
**Technology**: SQLite (initially), upgradeable to PostgreSQL.

## 1. Overview
The database serves as the single source of truth for the archive website. It links **Works** (abstract musical compositions) to **Files** (concrete digital assets like PDFs).

## 2. Table Definitions

### `works`
Represents a musical composition.
| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | Auto-incrementing ID |
| `work_number` | TEXT | The catalog number (e.g., "1", "14a", "1975"). Unique index. |
| `title` | TEXT | Main title of the work (e.g., "Psalm 23"). |
| `sort_title` | TEXT | Title for sorting (e.g., "Psalm 023"). |
| `composer` | TEXT | Default "Emanuel Vogt". |
| `year` | INTEGER | Year of composition. |
| `genre` | TEXT | e.g., "Psalm", "Choral", "Organ". |
| `instrumentation` | TEXT | e.g., "SATB", "Orgel". |
| `notes` | TEXT | Any additional metadata. |
| `created_at` | DATETIME | Record creation timestamp. |

### `files`
Represents a digital file in the archive.
| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | Auto-incrementing ID |
| `work_id` | INTEGER FK | References `works(id)`. |
| `filename` | TEXT | e.g., "14a - Hör, hör.pdf". |
| `filepath` | TEXT | Relative path (e.g., "files/Werke.../14a.pdf"). |
| `file_type` | TEXT | "pdf", "jpg", "mxl". |
| `size_bytes` | INTEGER | File size. |
| `page_count` | INTEGER | Number of pages (if PDF). |
| `width` | INTEGER | Width in pixels/points. |
| `height` | INTEGER | Height in pixels/points. |
| `dpi` | INTEGER | Estimated DPI. |
| `is_public` | BOOLEAN | Visibility toggle (default True). |

### `collections` (Optional for later)
Groupings like "Christmas Oratorio" or "Juvenilia".
| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | |
| `name` | TEXT | |
| `description` | TEXT | |

### `collection_items`
Join table.
| Field | Type | Description |
|-------|------|-------------|
| `collection_id` | INTEGER FK | |
| `work_id` | INTEGER FK | |

## 3. Indexes
-   `works.work_number`: Unique, indexed for fast lookup.
-   `works.title`: Indexed for search.
-   `files.work_id`: Indexed for joins.

## 4. Implementation Plan
1.  **Init Script**: Python script to create the SQLite DB.
2.  **Import Script**: Python script to read `file_inventory.csv` and populate `works` and `files`.
    -   Logic: Extract `work_number` from CSV. Create `Work` if not exists. Add `File`.
3.  **Validation**: Check for orphan files or works with no files.
