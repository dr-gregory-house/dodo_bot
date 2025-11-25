#!/bin/bash

# Initial Deployment Setup Script for Ubuntu 24
# Run this script on the cloud server after cloning the repository

set -e

echo "========================================="
echo "Dodo Bot - Initial Setup"
echo "========================================="
echo ""

# Check if running on Ubuntu
if [ ! -f /etc/os-release ] || ! grep -q "Ubuntu" /etc/os-release; then
    echo "Warning: This script is designed for Ubuntu 24. Proceed with caution."
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "Error: Python 3.10 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python version: $PYTHON_VERSION"
echo ""

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip git curl

echo "✓ System dependencies installed"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "✓ Python dependencies installed"
echo ""

# Create required directories
echo "Creating required directories..."
mkdir -p logs data
echo "✓ Directories created"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠ WARNING: .env file not found!"
    echo "Please create .env file with the following variables:"
    echo "  BOT_TOKEN=your_token_here"
    echo "  GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json"
    echo "  SPREADSHEET_ID=your_spreadsheet_id"
    echo "  GEMINI_API_KEY=your_gemini_key"
    echo ""
    read -p "Do you want to create .env now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        nano .env
    fi
else
    echo "✓ .env file found"
fi
echo ""

# Check for service account file
if [ ! -f "service_account.json" ]; then
    echo "⚠ WARNING: service_account.json not found!"
    echo "Please copy your Google Service Account JSON file to this directory"
    echo ""
else
    echo "✓ service_account.json found"
fi
echo ""

# Set up systemd services
echo "Setting up systemd services..."
read -p "Install systemd services? This requires sudo access. (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Update service files with current user and path
    CURRENT_USER=$(whoami)
    CURRENT_DIR=$(pwd)
    
    sudo sed -e "s|User=ubuntu|User=$CURRENT_USER|g" \
             -e "s|/home/ubuntu/dodo_bot|$CURRENT_DIR|g" \
             deployment/dodo-bot.service > /tmp/dodo-bot.service
    
    sudo sed -e "s|User=ubuntu|User=$CURRENT_USER|g" \
             -e "s|/home/ubuntu/dodo_bot|$CURRENT_DIR|g" \
             deployment/dodo-webapp.service > /tmp/dodo-webapp.service
    
    sudo cp /tmp/dodo-bot.service /etc/systemd/system/
    sudo cp /tmp/dodo-webapp.service /etc/systemd/system/
    
    sudo systemctl daemon-reload
    sudo systemctl enable dodo-bot
    sudo systemctl enable dodo-webapp
    
    echo "✓ Systemd services installed and enabled"
    echo ""
    
    read -p "Start services now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start dodo-bot
        sudo systemctl start dodo-webapp
        
        echo ""
        echo "Service status:"
        sudo systemctl status dodo-bot --no-pager -l | head -n 10
        echo ""
        sudo systemctl status dodo-webapp --no-pager -l | head -n 10
    fi
fi
echo ""

# Set up automatic backups
echo "Setting up automatic backups..."
read -p "Add daily backup cron job (3 AM)? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    CURRENT_DIR=$(pwd)
    CRON_CMD="0 3 * * * $CURRENT_DIR/deployment/backup.sh >> $CURRENT_DIR/logs/backup.log 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "backup.sh"; then
        echo "✓ Backup cron job already exists"
    else
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo "✓ Backup cron job added"
    fi
fi
echo ""

echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Verify .env configuration"
echo "2. Copy service_account.json if not done"
echo "3. Check service status: sudo systemctl status dodo-bot dodo-webapp"
echo "4. View logs: sudo journalctl -u dodo-bot -f"
echo "5. Test web app: curl http://localhost:5001/health"
echo ""
echo "For more information, see DEPLOYMENT.md and MAINTENANCE.md"
