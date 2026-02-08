@echo off
REM Windows Encoding Diagnostic Script
REM This script must be run from the project root directory

echo ================================================================================
echo Windows Encoding Diagnostic Tool
echo ================================================================================
echo.

REM Check if we're in the correct directory
if not exist "data\archive.db" (
    echo ERROR: Database not found!
    echo.
    echo Please run this script from the project root directory:
    echo   C:\Users\vogt-\Documents\Git\emanuelvogt\
    echo.
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

echo Running diagnostic...
echo.

python scripts\diagnose_encoding_windows.py

echo.
echo ================================================================================
echo Diagnostic complete!
echo ================================================================================
echo.
echo Please send the entire output above to Nicolas.
echo.
pause
