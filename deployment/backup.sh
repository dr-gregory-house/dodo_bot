#!/bin/bash

# Dodo Bot Backup Script
# Backs up all data files and configurations

set -e

BOT_DIR="/home/ubuntu/dodo_bot"
BACKUP_DIR="/home/ubuntu/dodo_bot_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"

echo "Creating backup at $BACKUP_PATH..."

# Create backup directory
mkdir -p "$BACKUP_PATH"

# Backup data files
if [ -d "$BOT_DIR/data" ]; then
    echo "Backing up data files..."
    cp -r "$BOT_DIR/data" "$BACKUP_PATH/"
fi

# Backup .env file (contains credentials)
if [ -f "$BOT_DIR/.env" ]; then
    echo "Backing up .env file..."
    cp "$BOT_DIR/.env" "$BACKUP_PATH/"
fi

# Backup service account file if exists
if [ -f "$BOT_DIR/service_account.json" ]; then
    echo "Backing up service account..."
    cp "$BOT_DIR/service_account.json" "$BACKUP_PATH/"
fi

# Backup logs (last 7 days)
if [ -d "$BOT_DIR/logs" ]; then
    echo "Backing up recent logs..."
    mkdir -p "$BACKUP_PATH/logs"
    find "$BOT_DIR/logs" -type f -mtime -7 -exec cp {} "$BACKUP_PATH/logs/" \;
fi

# Create archive
echo "Creating compressed archive..."
cd "$BACKUP_DIR"
tar -czf "backup_$TIMESTAMP.tar.gz" "backup_$TIMESTAMP"
rm -rf "backup_$TIMESTAMP"

# Keep only last 7 backups
echo "Cleaning old backups..."
ls -t "$BACKUP_DIR"/backup_*.tar.gz | tail -n +8 | xargs -r rm

echo "Backup completed: backup_$TIMESTAMP.tar.gz"
echo "Backup location: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
