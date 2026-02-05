from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sqlite3
import os

app = FastAPI()

# Configuration
BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "archive"
DB_PATH = BASE_DIR / "data/archive.db"

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open(BASE_DIR / "app/index.html", "r") as f:
        return f.read()

@app.get("/api/works")
async def get_works(q: str = "", genre: str = "All"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = "SELECT id, work_number, title, genre FROM works WHERE 1=1"
    params = []
    
    if q:
        query += " AND (title LIKE ? OR work_number LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])
    
    if genre != "All":
        query += " AND genre = ?"
        params.append(genre)
    
    query += " ORDER BY CASE WHEN work_number LIKE 'P-%' THEN 1 ELSE 0 END, CAST(work_number AS INTEGER), work_number"
    
    c.execute(query, params)
    rows = c.fetchall()
    
    works = []
    for r in rows:
        works.append({
            "id": r[0],
            "work_number": r[1],
            "title": r[2],
            "genre": r[3]
        })
    
    conn.close()
    return works

@app.get("/api/work/{work_id}")
async def get_work_detail(work_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get Work
    c.execute("SELECT id, work_number, title, genre FROM works WHERE id = ?", (work_id,))
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
        "files": files
    }

@app.get("/pdf/{file_id}")
async def get_pdf(file_id: int):
    conn = sqlite3.connect(DB_PATH)
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
    c = conn.cursor()
    c.execute("SELECT DISTINCT genre FROM works WHERE genre IS NOT NULL")
    genres = [r[0] for r in c.fetchall()]
    conn.close()
    return ["All"] + sorted(genres)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
