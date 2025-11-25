# Maintenance Guide

Operational guide for managing the Dodo Pizza Bot in production.

## Service Management

### Starting Services

```bash
# Start bot
sudo systemctl start dodo-bot

# Start web app
sudo systemctl start dodo-webapp

# Start both
sudo systemctl start dodo-bot dodo-webapp
```

### Stopping Services

```bash
# Stop bot
sudo systemctl stop dodo-bot

# Stop web app
sudo systemctl stop dodo-webapp

# Stop both
sudo systemctl stop dodo-bot dodo-webapp
```

### Restarting Services

```bash
# Restart bot
sudo systemctl restart dodo-bot

# Restart web app
sudo systemctl restart dodo-webapp

# Restart both
sudo systemctl restart dodo-bot dodo-webapp
```

### Checking Status

```bash
# Check bot status
sudo systemctl status dodo-bot

# Check web app status
sudo systemctl status dodo-webapp

# Check if services are enabled (start on boot)
sudo systemctl is-enabled dodo-bot
sudo systemctl is-enabled dodo-webapp
```

## Log Management

### Viewing Logs

```bash
# View bot logs (last 100 lines)
sudo journalctl -u dodo-bot -n 100

# View web app logs (last 100 lines)
sudo journalctl -u dodo-webapp -n 100

# Follow bot logs in real-time
sudo journalctl -u dodo-bot -f

# View logs from specific time
sudo journalctl -u dodo-bot --since "2025-11-25 10:00:00"

# View application log files
tail -f /home/ubuntu/dodo_bot/logs/dodo_bot.log
tail -f /home/ubuntu/dodo_bot/logs/webapp.log

# View error logs only
tail -f /home/ubuntu/dodo_bot/logs/dodo_bot_errors.log
```

### Log Rotation

Logs are automatically rotated:
- **Application logs**: 10MB per file, 5 backups kept
- **Systemd logs**: Managed by journald (default 4GB limit)

To manually rotate systemd logs:

```bash
sudo journalctl --vacuum-time=7d  # Keep last 7 days
sudo journalctl --vacuum-size=500M  # Keep max 500MB
```

## Updating the Bot

### Automatic Update (Recommended)

```bash
cd /home/ubuntu/dodo_bot
./deployment/update.sh
```

This script will:
1. Create a backup
2. Pull latest code from git
3. Update dependencies
4. Restart both services
5. Show status

### Manual Update

```bash
# 1. Create backup
./deployment/backup.sh

# 2. Pull latest code
git pull origin main

# 3. Activate virtual environment
source venv/bin/activate

# 4. Update dependencies
pip install -r requirements.txt --upgrade

# 5. Restart services
sudo systemctl restart dodo-bot dodo-webapp
```

## Backup and Restore

### Creating Backups

```bash
# Manual backup
cd /home/ubuntu/dodo_bot
./deployment/backup.sh
```

Backups are stored in `/home/ubuntu/dodo_bot_backups/` and include:
- All data files (`data/` directory)
- Environment configuration (`.env`)
- Google service account file
- Recent logs (last 7 days)

### Restoring from Backup

```bash
# 1. Stop services
sudo systemctl stop dodo-bot dodo-webapp

# 2. Navigate to backup directory
cd /home/ubuntu/dodo_bot_backups

# 3. List available backups
ls -lh backup_*.tar.gz

# 4. Extract backup
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz

# 5. Copy files back
cp -r backup_YYYYMMDD_HHMMSS/data/* /home/ubuntu/dodo_bot/data/
cp backup_YYYYMMDD_HHMMSS/.env /home/ubuntu/dodo_bot/
cp backup_YYYYMMDD_HHMMSS/service_account.json /home/ubuntu/dodo_bot/

# 6. Restart services
sudo systemctl start dodo-bot dodo-webapp
```

## Common Issues and Solutions

### Bot Not Starting

**Check logs:**
```bash
sudo journalctl -u dodo-bot -n 50
```

**Common causes:**
1. **Missing BOT_TOKEN**: Check `.env` file
2. **Python errors**: Check error log `/home/ubuntu/dodo_bot/logs/dodo_bot_errors.log`
3. **Permission issues**: Ensure files are readable by `ubuntu` user

**Solution:**
```bash
# Verify environment
cat /home/ubuntu/dodo_bot/.env | grep BOT_TOKEN

# Check file permissions
ls -l /home/ubuntu/dodo_bot/.env

# Fix permissions if needed
chmod 600 /home/ubuntu/dodo_bot/.env
```

### Web App Not Responding

**Check if running:**
```bash
sudo systemctl status dodo-webapp
curl http://localhost:5001/health
```

**Common causes:**
1. **Port already in use**: Check with `sudo netstat -tulpn | grep 5001`
2. **Gunicorn not installed**: Reinstall dependencies
3. **Import errors**: Check logs

**Solution:**
```bash
# Restart web app
sudo systemctl restart dodo-webapp

# If still failing, check logs
sudo journalctl -u dodo-webapp -n 100
```

### Notifications Not Working

**Check:**
1. **Job queue enabled**: Look for "Scheduler started" in logs
2. **Time zone correct**: Should be Europe/Moscow
3. **Group configured**: Check `data/group.json`

**Solution:**
```bash
# Restart bot to reinitialize scheduler
sudo systemctl restart dodo-bot

# Verify scheduler started
sudo journalctl -u dodo-bot | grep "Scheduler"
```

### High Memory Usage

**Check memory usage:**
```bash
systemctl status dodo-bot | grep Memory
systemctl status dodo-webapp | grep Memory
```

**Solution:**
```bash
# Restart services to clear memory
sudo systemctl restart dodo-bot dodo-webapp

# If persistent, check for memory leaks in logs
```

### Database/Sheets Connection Issues

**Check:**
1. **Service account file exists**: `/home/ubuntu/dodo_bot/service_account.json`
2. **Spreadsheet ID correct**: Check `.env`
3. **Network connectivity**

**Solution:**
```bash
# Verify credentials
ls -l /home/ubuntu/dodo_bot/service_account.json

# Check spreadsheet ID
cat .env | grep SPREADSHEET_ID

# Test network
ping sheets.googleapis.com
```

## Monitoring

### Health Checks

```bash
# Bot running check
systemctl is-active dodo-bot

# Web app health
curl http://localhost:5001/health

# Quick status of both
systemctl is-active dodo-bot && echo "Bot: OK" || echo "Bot: FAILED"
systemctl is-active dodo-webapp && echo "WebApp: OK" || echo "WebApp: FAILED"
```

### Resource Usage

```bash
# View CPU and memory
top -p $(pgrep -f "python.*main.py") $(pgrep -f gunicorn)

# Detailed systemd resource info
systemctl status dodo-bot dodo-webapp
```

## Configuration Changes

### Updating Environment Variables

```bash
# 1. Edit .env file
nano /home/ubuntu/dodo_bot/.env

# 2. Restart services to apply
sudo systemctl restart dodo-bot dodo-webapp
```

### Modifying Service Configuration

```bash
# 1. Edit service file
sudo nano /etc/systemd/system/dodo-bot.service

# 2. Reload systemd
sudo systemctl daemon-reload

# 3. Restart service
sudo systemctl restart dodo-bot
```

## Emergency Procedures

### Complete System Reset

```bash
# 1. Stop all services
sudo systemctl stop dodo-bot dodo-webapp

# 2. Create emergency backup
./deployment/backup.sh

# 3. Clear logs
rm /home/ubuntu/dodo_bot/logs/*.log*

# 4. Reset data (CAREFUL!)
# Only if you want to clear all data
rm /home/ubuntu/dodo_bot/data/*.json

# 5. Restart services
sudo systemctl start dodo-bot dodo-webapp
```

### Full Reinstall

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete installation steps.

## Support

For issues not covered here:
1. Check application logs in `/home/ubuntu/dodo_bot/logs/`
2. Check systemd logs with `journalctl`
3. Review recent code changes in git history
