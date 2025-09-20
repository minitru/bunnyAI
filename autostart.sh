#!/bin/bash

# Alternative autostart script using @reboot in crontab
# Add this line to crontab: @reboot /Users/sean/src/bunnyAI/autostart.sh

# Log file for startup
LOG_FILE="/Users/sean/src/bunnyAI/startup.log"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log "Starting Jessica's Crabby Editor autostart script"

# Wait for network to be available
sleep 30

# Change to script directory
cd /Users/sean/src/bunnyAI

# Load environment variables
if [ -f ".env" ]; then
    log "Loading environment variables"
    export $(grep -v '^#' .env | xargs)
fi

# Activate virtual environment
if [ -d "venv" ]; then
    log "Activating virtual environment"
    source venv/bin/activate
else
    log "ERROR: Virtual environment not found"
    exit 1
fi

# Start the application
log "Starting application"
nohup python start_web.py >> "$LOG_FILE" 2>&1 &

# Get the PID and log it
PID=$!
log "Application started with PID: $PID"
echo $PID > /Users/sean/src/bunnyAI/bunny-ai.pid

log "Autostart script completed"
