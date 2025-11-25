#!/bin/bash

# Dodo Bot Startup Script
# This script ensures all prerequisites are met before starting the bot

set -e

BOT_DIR="/home/ubuntu/dodo_bot"
VENV_DIR="$BOT_DIR/venv"

echo "Starting Dodo Bot..."

# Check if running from correct directory
if [ ! -f "$BOT_DIR/main.py" ]; then
    echo "Error: main.py not found. Please run from correct directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if .env file exists
if [ ! -f "$BOT_DIR/.env" ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Check for required environment variables
source "$BOT_DIR/.env"
if [ -z "$BOT_TOKEN" ]; then
    echo "Error: BOT_TOKEN not set in .env"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p "$BOT_DIR/logs"

# Create data directory if it doesn't exist
mkdir -p "$BOT_DIR/data"

echo "All checks passed. Starting bot..."
cd "$BOT_DIR"
python main.py
