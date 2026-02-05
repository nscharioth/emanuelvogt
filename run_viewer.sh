#!/bin/bash
# Script to run the Emanuel Vogt Digital Archive Viewer
echo "🚀 Starting Emanuel Vogt Digital Archive Viewer..."

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment (venv) not found. Please follow SHARING_INSTRUCTIONS.md"
    exit 1
fi

source venv/bin/activate
python3 app/backend.py
