@echo off
echo 🚀 Starting Emanuel Vogt Digital Archive Viewer...

if not exist venv (
    echo ❌ Virtual environment (venv) not found. Please follow SHARING_INSTRUCTIONS.md
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate
python app/backend.py
pause
