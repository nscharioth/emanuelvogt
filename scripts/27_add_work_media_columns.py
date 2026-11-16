#!/usr/bin/env python3
"""
Script 27: Add work media/comment columns

Adds the columns used by the WordPress plugin "EmanuelVogt Werkverzeichnis"
to the works table, so the repository copy of archive.db has the same schema
as the server copy:

  comment                      TEXT     free-text note shown in the work dialog
  transcription_attachment_id  INTEGER  WP media-library ID of the transcribed PDF ("Neusatz")
  audio_attachment_id          INTEGER  WP media-library ID of the recording ("Aufnahme")
  updated_at                   TEXT     set by the plugin on every change (UTC)
  transcription2_attachment_id INTEGER  second transcribed PDF (plugin schema version 2)
  audio2_attachment_id         INTEGER  second recording (plugin schema version 2)

Note: SQLite does not allow non-constant defaults in ALTER TABLE, so
updated_at has no default. The ALTER statements are identical to the ones
in wp-plugin/evogt-works-admin/includes/schema.php.
"""

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "archive.db"

COLUMNS = {
    "comment": "ALTER TABLE works ADD COLUMN comment TEXT",
    "transcription_attachment_id": "ALTER TABLE works ADD COLUMN transcription_attachment_id INTEGER",
    "audio_attachment_id": "ALTER TABLE works ADD COLUMN audio_attachment_id INTEGER",
    "updated_at": "ALTER TABLE works ADD COLUMN updated_at TEXT",
    "transcription2_attachment_id": "ALTER TABLE works ADD COLUMN transcription2_attachment_id INTEGER",
    "audio2_attachment_id": "ALTER TABLE works ADD COLUMN audio2_attachment_id INTEGER",
}
INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_works_audio_attachment ON works(audio_attachment_id)",
    "CREATE INDEX IF NOT EXISTS idx_works_audio2_attachment ON works(audio2_attachment_id)",
]


def add_columns(db_path: Path) -> int:
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    existing = {row[1] for row in cursor.execute("PRAGMA table_info(works)")}
    if not existing:
        print("❌ Table 'works' not found")
        conn.close()
        return 1

    missing = {name: sql for name, sql in COLUMNS.items() if name not in existing}
    if not missing:
        print("✅ All columns already present, nothing to do")
    else:
        backup = db_path.with_name(f"archive_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
        shutil.copy2(db_path, backup)
        print(f"💾 Backup written: {backup.name}")

        for name, sql in missing.items():
            cursor.execute(sql)
            print(f"➕ Added column: {name}")

    for sql in INDEX_SQL:
        cursor.execute(sql)
    conn.commit()

    print("\nSchema of 'works':")
    for col in cursor.execute("PRAGMA table_info(works)"):
        print(f"  - {col[1]} ({col[2]})")

    conn.close()
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DB_PATH
    sys.exit(add_columns(target))
