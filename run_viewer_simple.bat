@echo off
REM Simplified version without venv requirement
REM Automatically fixes database naming and starts server

echo ================================================================================
echo EMANUEL VOGT DIGITAL ARCHIVE VIEWER - QUICK START
echo ================================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM ============================================================================
REM Step 1: Check and fix database naming
REM ============================================================================
echo [1/3] Database Check...
echo.

if exist "data\archive.db" (
    for %%A in ("data\archive.db") do (
        set size=%%~zA
        if %%~zA GTR 100000 (
            echo ✅ Database OK: data\archive.db ^(%%~zA bytes^)
        ) else (
            echo ⚠️  Database too small: %%~zA bytes ^(should be ~800 KB^)
            echo     Please run: update_windows.bat
            pause
            exit /b 1
        )
    )
) else (
    echo ⚠️  Database "archive.db" not found
    echo     Checking for naming issue...
    
    if exist "data\archive" (
        echo     Found: data\archive ^(without .db extension^)
        echo     Auto-fixing: Renaming to archive.db...
        ren "data\archive" "archive.db"
        
        if exist "data\archive.db" (
            echo ✅ Successfully fixed: data\archive.db
        ) else (
            echo ❌ Rename failed! Please run manually:
            echo     ren data\archive archive.db
            pause
            exit /b 1
        )
    ) else (
        echo ❌ Database missing!
        echo.
        echo Please follow one of these solutions:
        echo   1. Run: update_windows.bat
        echo   2. See: WINDOWS_DATENBANK_FEHLT.txt
        pause
        exit /b 1
    )
)
echo.

REM ============================================================================
REM Step 2: Check Python and packages
REM ============================================================================
echo [2/3] Python Check...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo     Please install Python 3.10+ from: https://www.python.org
    echo     Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python --version
echo.

REM Quick check if FastAPI is installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Required packages not installed!
    echo     Installing now... ^(this may take 1-2 minutes^)
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Installation failed!
        pause
        exit /b 1
    )
    echo ✅ Packages installed successfully
    echo.
)

REM ============================================================================
REM Step 3: Start server
REM ============================================================================
echo [3/3] Starting Server...
echo ================================================================================
echo.
echo Server will start on: http://localhost:8000
echo.
echo ⚠️  DO NOT CLOSE THIS WINDOW while using the Archive Viewer!
echo     To stop the server: Press Ctrl+C
echo.
echo ================================================================================
echo.

python -m uvicorn app.backend:app --host 0.0.0.0 --port 8000

REM If server stops
echo.
echo ================================================================================
echo Server stopped.
echo ================================================================================
pause
