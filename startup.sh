#!/bin/bash

# Jessica's Crabby Editor Startup Script
# This script ensures proper environment setup and starts the AI system

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Warning: Virtual environment not found at venv/"
fi

# Check if required files exist
if [ ! -f "start_web.py" ]; then
    echo "Error: start_web.py not found!"
    exit 1
fi

if [ ! -f "multi_book_rag.py" ]; then
    echo "Error: multi_book_rag.py not found!"
    exit 1
fi

# Start the application
echo "Starting Jessica's Crabby Editor..."
echo "Working directory: $(pwd)"
echo "Python path: $(which python)"
echo "Timestamp: $(date)"

# Use start_web.py for production (no debug mode)
python start_web.py
