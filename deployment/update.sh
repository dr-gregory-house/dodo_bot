#!/bin/bash

# Dodo Bot Update Script
# Safely updates the bot code and restarts services

set -e

BOT_DIR="/home/ubuntu/dodo_bot"

echo "Updating Dodo Bot..."

cd "$BOT_DIR"

# Create backup before update
echo "Creating pre-update backup..."
./deployment/backup.sh

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# Update dependencies
echo "Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart services
echo "Restarting bot service..."
sudo systemctl restart dodo-bot

echo "Restarting web app service..."
sudo systemctl restart dodo-webapp

# Check status
sleep 3
echo ""
echo "Bot status:"
sudo systemctl status dodo-bot --no-pager -l | head -n 10

echo ""
echo "Web app status:"
sudo systemctl status dodo-webapp --no-pager -l | head -n 10

echo ""
echo "Update completed successfully!"
