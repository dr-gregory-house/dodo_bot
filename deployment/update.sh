#!/bin/bash

# Dodo Bot Update Script
# Safely updates the bot code and restarts services

set -e

BOT_DIR="/home/ubuntu/dodo_bot"

echo "Updating Dodo Bot..."

cd "$BOT_DIR"

# External data directory
EXTERNAL_DATA_DIR="$HOME/dodo_bot_data"

echo "Ensuring external data directory exists..."
mkdir -p "$EXTERNAL_DATA_DIR"

# Copy any NEW default data files from the repo to the external dir
# -n (no-clobber) ensures we DO NOT overwrite existing production data
if [ -d "data" ]; then
    echo "Populating new default data files..."
    cp -rn data/* "$EXTERNAL_DATA_DIR/" || true
fi

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
    # Update to latest code (use reset to handle local changes from deploy.yml)
    echo "Updating to latest code..."
    git fetch origin
    git reset --hard origin/main
fi

# Link data directory
echo "Linking data directory..."
rm -rf data
ln -s "$EXTERNAL_DATA_DIR" data

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
