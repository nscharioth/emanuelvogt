from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sqlite3
import os
import re

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
    
    if q:
        # Exact match for work_number, partial match for title
        query += " AND (title LIKE ? OR work_number = ?)"
        params.extend([f"%{q}%", q])
    
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
    
    # Sort by Database ID (which puts Psalms P-1 through P-206 at the end, IDs 2080-2323)
    # Regular works 1-2099 have IDs 1-2039
    query += " ORDER BY id"
    
    c.execute(query, params)
    rows = c.fetchall()
    
    works = []
    for r in rows:
        works.append({
            "id": r[0],
            "work_number": r[1],
            "title": r[2],
            "genre": r[3],
            "instrumentation": r[4]
        })
    
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
    
    # Get Files
    c.execute("SELECT id, filename, filepath, file_type, size_bytes FROM files WHERE work_id = ?", (work_id,))
    file_rows = c.fetchall()
    
    files = []
    for f in file_rows:
        files.append({
            "id": f[0],
            "filename": f[1],
            "filepath": f[2],
            "type": f[3],
            "size": f[4]
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
    c.execute("SELECT filepath FROM files WHERE id = ?", (file_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = ARCHIVE_DIR / row[0]
    if not file_path.exists():
        # Fallback for folder location
        raise HTTPException(status_code=404, detail=f"File not found on disk: {row[0]}")
        
    return FileResponse(file_path, media_type="application/pdf")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
