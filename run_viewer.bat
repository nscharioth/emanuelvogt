@echo off
echo 🚀 Starting Emanuel Vogt Digital Archive Viewer...
echo.

REM ============================================================================
REM Check and fix database naming (Windows hides .db extension)
REM ============================================================================
echo [1/3] Checking database...

if exist "data\archive.db" (
    echo ✅ Database found: data\archive.db
) else (
    if exist "data\archive" (
        echo ⚠️  Database found without .db extension!
        echo     Fixing: data\archive → data\archive.db
        ren "data\archive" "archive.db"
        
        if exist "data\archive.db" (
            echo ✅ Successfully renamed to archive.db
        ) else (
            echo ❌ Failed to rename database!
            echo     Please run: check_database_windows.bat
            pause
            exit /b 1
        )
    ) else (
        echo ❌ Database not found!
        echo     Expected: data\archive.db
        echo.
        echo     Please see: WINDOWS_DATENBANK_FEHLT.txt
        echo     Or run: update_windows.bat
        pause
        exit /b 1
    )
)
echo.

REM ============================================================================
REM Check and setup virtual environment
REM ============================================================================
echo [2/3] Checking virtual environment...

set USE_VENV=0

if not exist "venv" (
    echo ⚠️  Virtual environment not found. Attempting to create...
    echo.
    
    REM Check if Python is available
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python not found! Please install Python first.
        pause
        exit /b 1
    )
    
    REM Try to create virtual environment
    echo Creating virtual environment...
    python -m venv venv
    
    if exist "venv\Scripts\activate.bat" (
        echo ✅ Virtual environment created successfully
        echo Installing dependencies...
        call venv\Scripts\activate.bat
        pip install -r requirements.txt
        if errorlevel 1 (
            echo ⚠️  Some dependencies failed to install, but continuing...
        )
        set USE_VENV=1
    ) else (
        echo ⚠️  Could not create virtual environment
        echo     Will use system Python as fallback
        set USE_VENV=0
    )
) else (
    echo ✅ Virtual environment found
    set USE_VENV=1
)
echo.

REM ============================================================================
REM Start server
REM ============================================================================
echo [3/3] Starting server...
echo.

if %USE_VENV%==1 (
    echo Using virtual environment
) else (
    echo Using system Python (fallback)
)

echo.
echo ⚠️  DO NOT CLOSE THIS WINDOW while using the Archive Viewer!
echo     Server will be available at: http://localhost:8000
echo     To stop the server: Press Ctrl+C in this window
echo.
echo Opening browser in 3 seconds...
echo.

REM Wait a moment before opening browser
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:8000

REM Start server
if %USE_VENV%==1 (
    call venv\Scripts\activate.bat
    python -m uvicorn app.backend:app --host 0.0.0.0 --port 8000
) else (
    python -m uvicorn app.backend:app --host 0.0.0.0 --port 8000
)

REM If server stops
echo.
echo Server stopped.
pause
