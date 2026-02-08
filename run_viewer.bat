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
REM Check virtual environment
REM ============================================================================
echo [2/3] Checking virtual environment...

if not exist venv (
    echo ❌ Virtual environment (venv) not found!
    echo     Please follow SHARING_INSTRUCTIONS.md
    echo     Or run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✅ Virtual environment found
echo.

REM ============================================================================
REM Start server
REM ============================================================================
echo [3/3] Starting server...
echo.
echo ⚠️  DO NOT CLOSE THIS WINDOW while using the Archive Viewer!
echo     Server will be available at: http://localhost:8000
echo     To stop the server: Press Ctrl+C in this window
echo.
echo Opening browser in 3 seconds...
echo.

REM Start server in background and wait a moment
start /B call venv\Scripts\activate
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:8000

REM Start server in foreground
call venv\Scripts\activate
python -m uvicorn app.backend:app --host 0.0.0.0 --port 8000

REM If server stops
echo.
echo Server stopped.
pause
