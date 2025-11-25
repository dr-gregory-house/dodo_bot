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

# Check if git repository exists, initialize if needed
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git remote add origin https://github.com/dr-gregory-house/dodo_bot.git
    git fetch origin
    # Reset to match remote (preserves .env and service_account.json which are in .gitignore)
    git reset --hard origin/main
    echo "Git repository initialized and synced."
else
    # Pull latest code
    echo "Pulling latest code..."
    git pull origin main
fi

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
