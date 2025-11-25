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

# Preserve production data files
TEMP_DATA_DIR="/tmp/dodo_bot_data_$$"
PRODUCTION_FILES="group.json medical_info.json users.json not_subscribed.json notifications.json on_shift.json ratings.json"

echo "Preserving production data files..."
mkdir -p "$TEMP_DATA_DIR"
for file in $PRODUCTION_FILES; do
    if [ -f "data/$file" ]; then
        cp "data/$file" "$TEMP_DATA_DIR/"
    fi
done

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

# Restore production data files
echo "Restoring production data files..."
for file in $PRODUCTION_FILES; do
    if [ -f "$TEMP_DATA_DIR/$file" ]; then
        cp "$TEMP_DATA_DIR/$file" "data/"
    fi
done
rm -rf "$TEMP_DATA_DIR"

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
