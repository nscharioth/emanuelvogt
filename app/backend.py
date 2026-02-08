from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sqlite3
import os
import re
from PyPDF2 import PdfReader, PdfWriter
import io
import unicodedata

app = FastAPI()

# Configuration
BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "archive"
DB_PATH = BASE_DIR / "data/archive.db"
MUSICXML_DIR = BASE_DIR / "data/manual"

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open(BASE_DIR / "app/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/favicon.ico")
async def get_favicon():
    # Return a simple 1x1 transparent PNG as favicon
    return Response(
        content=bytes.fromhex('89504e470d0a1a0a0000000d494844520000000100000001010300000025db56ca00000003504c5445000000a77a3dda0000000174524e530040e6d8660000000a4944415408d76360000000020001e221bc330000000049454e44ae426082'),
        media_type="image/x-icon"
    )

@app.get("/musicxml-player", response_class=HTMLResponse)
async def get_musicxml_player():
    with open(BASE_DIR / "app/musicxml_player.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/works")
async def get_works(q: str = "", genre: str = "All", instrumentation: str = "All"):
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = lambda x: x.decode('utf-8', errors='replace')
    c = conn.cursor()
    
    query = "SELECT id, work_number, title, genre, instrumentation FROM works WHERE 1=1"
    params = []
    
    # Note: We'll do text search in Python to handle Unicode normalization properly
    search_term = None
    if q:
        # Normalize search term to NFC (precomposed) for consistent comparison
        search_term = unicodedata.normalize('NFC', q).lower()
    
    if genre != "All":
        query += " AND genre = ?"
        params.append(genre)
    
    if instrumentation != "All":
        # Match works where instrumentation contains the selected instrument
        # Handles: "Sopran", "Sopran, Alt", "Alt, Sopran", etc.
        query += " AND (instrumentation LIKE ? OR instrumentation LIKE ? OR instrumentation LIKE ? OR instrumentation = ?)"
        params.extend([
            f"{instrumentation},%",  # Start: "Sopran, ..."
            f"%, {instrumentation},%",  # Middle: "..., Sopran, ..."
            f"%, {instrumentation}",  # End: "..., Sopran"
            instrumentation  # Exact match: "Sopran"
        ])
    
    # Don't sort in SQL - we'll sort in Python for proper alphanumeric ordering
    c.execute(query, params)
    rows = c.fetchall()
    
    works = []
    for r in rows:
        # Apply text search in Python with proper Unicode normalization
        if search_term:
            # Normalize database values to NFC for consistent comparison
            title_normalized = unicodedata.normalize('NFC', r[2] or '').lower()
            work_num_normalized = unicodedata.normalize('NFC', r[1] or '').lower()
            
            # Check if search term matches (case-insensitive, normalized)
            if search_term not in title_normalized and search_term != work_num_normalized:
                continue
        
        works.append({
            "id": r[0],
            "work_number": r[1],
            "title": r[2],
            "genre": r[3],
            "instrumentation": r[4]
        })
    
    # Sort by work_number with natural sorting (1, 2, 3a, 3b, 10, 11, P-1, P-2, etc.)
    def natural_sort_key(work):
        work_num = work["work_number"] or ""
        
        # Split into parts: numbers and letters
        # Examples: "14a" -> [(0,14), (1,"a")], "P-123" -> [(1,"P"), (1,"-"), (0,123)]
        parts = []
        current_num = ""
        current_alpha = ""
        
        for char in work_num:
            if char.isdigit():
                if current_alpha:
                    parts.append((1, current_alpha))  # (1, str) for alpha
                    current_alpha = ""
                current_num += char
            else:
                if current_num:
                    parts.append((0, int(current_num)))  # (0, int) for numbers
                    current_num = ""
                current_alpha += char
        
        # Add remaining
        if current_num:
            parts.append((0, int(current_num)))
        if current_alpha:
            parts.append((1, current_alpha))
        
        # This ensures proper sorting: numbers come before letters at each position
        # So: 1 < 2 < 3 < 3a < 3b < 10 < 14 < 14a < P-1 < P-10
        return tuple(parts) if parts else ((1, work_num),)
    
    works.sort(key=natural_sort_key)
    
    conn.close()
    return works

@app.get("/api/work/{work_id}")
async def get_work_detail(work_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = lambda x: x.decode('utf-8', errors='replace')
    c = conn.cursor()
    
    # Get Work
    c.execute("SELECT id, work_number, title, genre, instrumentation, has_musicxml FROM works WHERE id = ?", (work_id,))
    work_row = c.fetchone()
    if not work_row:
        raise HTTPException(status_code=404, detail="Work not found")
    
    # Get Files with rotation info
    c.execute("""
        SELECT f.id, f.filename, f.filepath, f.file_type, f.size_bytes, 
               COALESCE(r.rotation, 0) as rotation
        FROM files f
        LEFT JOIN pdf_rotations r ON f.id = r.file_id
        WHERE f.work_id = ?
    """, (work_id,))
    file_rows = c.fetchall()
    
    files = []
    for f in file_rows:
        files.append({
            "id": f[0],
            "filename": f[1],
            "filepath": f[2],
            "type": f[3],
            "size": f[4],
            "rotation": f[5] if len(f) > 5 else 0
        })
        
    conn.close()
    return {
        "id": work_row[0],
        "work_number": work_row[1],
        "title": work_row[2],
        "genre": work_row[3],
        "instrumentation": work_row[4],
        "has_musicxml": bool(work_row[5]) if len(work_row) > 5 else False,
        "files": files
    }

@app.get("/pdf/{file_id}")
async def get_pdf(file_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = lambda x: x.decode('utf-8', errors='replace')
    c = conn.cursor()
    
    # Get file paths (including new flat_path if available)
    c.execute("SELECT filepath, filename, flat_path, slug FROM files WHERE id = ?", (file_id,))
    row = c.fetchone()
    
    # Get saved rotation
    c.execute("SELECT rotation FROM pdf_rotations WHERE file_id = ?", (file_id,))
    rotation_row = c.fetchone()
    rotation = rotation_row[0] if rotation_row else 0
    
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="File not found in database")
    
    filepath_str = row[0]
    filename_from_db = row[1] if len(row) > 1 else None
    flat_path_str = row[2] if len(row) > 2 else None
    slug = row[3] if len(row) > 3 else None
    
    # HYBRID PATH RESOLUTION: Try flat/ first (preferred), fallback to files/
    file_path = None
    tried_paths = []
    
    # Strategy 1: Try flat/ archive (URL-safe, normalized)
    if flat_path_str:
        flat_full_path = ARCHIVE_DIR / flat_path_str
        tried_paths.append(('flat', str(flat_full_path)))
        if flat_full_path.exists():
            file_path = flat_full_path
    
    # Strategy 2: Try old files/ archive (backward compatibility)
    if not file_path and filepath_str:
        # Handle path separators for cross-platform compatibility
        relative_path = Path(filepath_str.replace('/', os.sep))
        old_full_path = ARCHIVE_DIR / relative_path
        tried_paths.append(('files (normalized)', str(old_full_path)))
        if old_full_path.exists():
            file_path = old_full_path
        else:
            # Try without path separator conversion
            alt_file_path = ARCHIVE_DIR / filepath_str
            tried_paths.append(('files (direct)', str(alt_file_path)))
            if alt_file_path.exists():
                file_path = alt_file_path
    
    # Strategy 3: Last resort - search by filename in expected directory
    if not file_path and filename_from_db:
        # Try to find in old location
        expected_dir = (ARCHIVE_DIR / Path(filepath_str)).parent
        if expected_dir.exists():
            tried_paths.append(('search', f"{expected_dir}/{filename_from_db}"))
            # Exact match
            possible_files = list(expected_dir.glob(filename_from_db))
            if possible_files:
                file_path = possible_files[0]
            else:
                # Case-insensitive search
                all_files = list(expected_dir.glob('*.pdf'))
                for f in all_files:
                    if f.name.lower() == filename_from_db.lower():
                        file_path = f
                        break
    
    # If still not found, raise detailed error
    if not file_path:
        error_detail = f"File not found. Tried {len(tried_paths)} locations:\n"
        for i, (method, path) in enumerate(tried_paths, 1):
            error_detail += f"{i}. [{method}] {path}\n"
        raise HTTPException(status_code=404, detail=error_detail.strip())
    
    # Determine media type based on file extension
    file_extension = file_path.suffix.lower()
    media_type_map = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
    }
    media_type = media_type_map.get(file_extension, 'application/pdf')
    is_image = file_extension in ['.jpg', '.jpeg', '.png', '.gif']
    
    # Set Content-Disposition header with original filename for downloads
    headers = {}
    if filename_from_db:
        # Encode filename properly for Content-Disposition header (RFC 5987)
        # Use ASCII fallback for filename and UTF-8 encoded filename* for modern browsers
        from urllib.parse import quote
        
        # Create ASCII-safe fallback (replace non-ASCII with underscore)
        ascii_filename = filename_from_db.encode('ascii', 'replace').decode('ascii').replace('?', '_')
        
        # URL-encode the UTF-8 filename for filename* parameter
        utf8_filename = quote(filename_from_db.encode('utf-8'))
        
        # RFC 5987: filename* parameter with encoding indicator
        headers["Content-Disposition"] = f'inline; filename="{ascii_filename}"; filename*=UTF-8\'\'{utf8_filename}'
    
    # For images, serve directly without rotation
    if is_image:
        return FileResponse(file_path, media_type=media_type, headers=headers)
    
    # For PDFs: If no rotation, serve file directly
    if rotation == 0:
        return FileResponse(file_path, media_type=media_type, headers=headers)
    
    # Apply rotation using PyPDF2 (only for PDFs)
    try:
        reader = PdfReader(str(file_path))
        writer = PdfWriter()
        
        for page in reader.pages:
            page.rotate(rotation)
            writer.add_page(page)
        
        # Write to memory buffer
        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)
        
        return Response(content=buffer.getvalue(), media_type=media_type, headers=headers)
    except Exception as e:
        # Fallback to original file if rotation fails
        return FileResponse(file_path, media_type=media_type, headers=headers)

@app.get("/pdf/by-slug/{slug}")
async def get_pdf_by_slug(slug: str):
    """
    Get PDF by URL-safe slug (e.g., '0528-improperion.pdf')
    This is the preferred method for web access - SEO friendly and human-readable.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = lambda x: x.decode('utf-8', errors='replace')
    c = conn.cursor()
    
    # Look up file by slug
    c.execute("SELECT id FROM files WHERE slug = ?", (slug,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"File with slug '{slug}' not found")
    
    file_id = row[0]
    
    # Delegate to existing PDF endpoint
    return await get_pdf(file_id)

@app.get("/api/genres")
async def get_genres():
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = lambda x: x.decode('utf-8', errors='replace')
    c = conn.cursor()
    c.execute("SELECT DISTINCT genre FROM works WHERE genre IS NOT NULL")
    genres = [r[0] for r in c.fetchall()]
    conn.close()
    return ["All"] + sorted(genres)

@app.get("/api/instrumentations")
async def get_instrumentations():
    """Get list of individual instruments from comma-separated instrumentation field."""
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = lambda x: x.decode('utf-8', errors='replace')
    c = conn.cursor()
    c.execute("SELECT DISTINCT instrumentation FROM works WHERE instrumentation IS NOT NULL")
    
    # Parse comma-separated values and flatten to individual instruments
    all_instruments = set()
    for (inst,) in c.fetchall():
        if inst:
            # Split by comma and trim whitespace
            parts = [p.strip() for p in inst.split(',')]
            all_instruments.update(parts)
    
    conn.close()
    return ["All"] + sorted(list(all_instruments))

@app.get("/api/musicxml/list")
async def get_musicxml_files():
    """Get list of available MusicXML files with work metadata."""
    if not MUSICXML_DIR.exists():
        return []
    
    files = []
    for file_path in MUSICXML_DIR.glob("*.musicxml"):
        # Extract work number from filename (e.g., "9 - Title.musicxml" -> "9")
        filename = file_path.name
        match = re.match(r'^([^-]+)\s*-', filename)
        work_number = match.group(1).strip() if match else None
        
        # Get work details from database if work_number exists
        work_title = None
        work_id = None
        if work_number:
            conn = sqlite3.connect(DB_PATH)
            conn.text_factory = lambda x: x.decode('utf-8', errors='replace')
            c = conn.cursor()
            c.execute("SELECT id, title FROM works WHERE work_number = ?", (work_number,))
            result = c.fetchone()
            conn.close()
            if result:
                work_id = result[0]
                work_title = result[1]
        
        files.append({
            "filename": filename,
            "work_number": work_number,
            "work_id": work_id,
            "work_title": work_title
        })
    
    return sorted(files, key=lambda x: x.get('work_number', ''))

@app.get("/api/musicxml/{filename}")
async def get_musicxml_file(filename: str):
    """Serve a MusicXML file."""
    file_path = MUSICXML_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="MusicXML file not found")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return Response(content=content, media_type="application/vnd.recordare.musicxml+xml")

@app.get("/api/pdf-rotation/{file_id}")
async def get_pdf_rotation(file_id: int):
    """Get the saved rotation for a PDF file."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT rotation FROM pdf_rotations WHERE file_id = ?", (file_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {"file_id": file_id, "rotation": result[0]}
    else:
        return {"file_id": file_id, "rotation": 0}

@app.post("/api/pdf-rotation/{file_id}")
async def set_pdf_rotation(file_id: int, request: Request):
    """Save the rotation for a PDF file."""
    data = await request.json()
    rotation = data.get("rotation", 0)
    
    # Validate rotation (must be 0, 90, 180, or 270)
    if rotation not in [0, 90, 180, 270]:
        raise HTTPException(status_code=400, detail="Rotation must be 0, 90, 180, or 270")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Insert or update
    c.execute("""
        INSERT OR REPLACE INTO pdf_rotations (file_id, rotation, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (file_id, rotation))
    
    conn.commit()
    conn.close()
    
    return {"file_id": file_id, "rotation": rotation, "saved": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
