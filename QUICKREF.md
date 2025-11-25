# Quick Reference - Dodo Bot Production

## Essential Commands

### Service Control
```bash
# Start
sudo systemctl start dodo-bot dodo-webapp

# Stop
sudo systemctl stop dodo-bot dodo-webapp

# Restart
sudo systemctl restart dodo-bot dodo-webapp

# Status
sudo systemctl status dodo-bot dodo-webapp
```

### View Logs
```bash
# Live logs
sudo journalctl -u dodo-bot -f
sudo journalctl -u dodo-webapp -f

# Application logs
tail -f ~/dodo_bot/logs/dodo_bot.log
tail -f ~/dodo_bot/logs/webapp.log
tail -f ~/dodo_bot/logs/dodo_bot_errors.log
```

### Maintenance
```bash
# Update bot
cd ~/dodo_bot && ./deployment/update.sh

# Create backup
cd ~/dodo_bot && ./deployment/backup.sh

# Restore from backup
cd ~/dodo_bot_backups
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz
sudo systemctl stop dodo-bot dodo-webapp
cp -r backup_*/data/* ~/dodo_bot/data/
sudo systemctl start dodo-bot dodo-webapp
```

### Health Checks
```bash
# Services running
systemctl is-active dodo-bot && echo "Bot: OK" || echo "Bot: FAILED"
systemctl is-active dodo-webapp && echo "WebApp: OK" || echo "WebApp: FAILED"

# Web app health
curl http://localhost:5001/health

# Resource usage
systemctl status dodo-bot dodo-webapp
```

## Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `.env` | `/home/ubuntu/dodo_bot/.env` | Environment variables |
| `service_account.json` | `/home/ubuntu/dodo_bot/` | Google credentials |
| Bot service | `/etc/systemd/system/dodo-bot.service` | Systemd config |
| WebApp service | `/etc/systemd/system/dodo-webapp.service` | Systemd config |

## Log Locations

| Log Type | Location |
|----------|----------|
| Bot logs | `/home/ubuntu/dodo_bot/logs/dodo_bot.log` |
| Error logs | `/home/ubuntu/dodo_bot/logs/dodo_bot_errors.log` |
| WebApp logs | `/home/ubuntu/dodo_bot/logs/webapp.log` |
| Systemd logs | `sudo journalctl -u dodo-bot` |
| Backup logs | `/home/ubuntu/dodo_bot/logs/backup.log` |

## Common Issues

| Issue | Quick Fix |
|-------|-----------|
| Bot not starting | Check `.env` file and BOT_TOKEN |
| Web app not responding | `sudo systemctl restart dodo-webapp` |
| Notifications not working | Check scheduler in logs, restart bot |
| High memory | Restart services |
| Database errors | Verify `service_account.json` and SPREADSHEET_ID |

## Ports & Endpoints

| Service | Port | Endpoint |
|---------|------|----------|
| Web App | 5001 | `http://localhost:5001` |
| Health Check | 5001 | `http://localhost:5001/health` |
| API Preps | 5001 | `http://localhost:5001/api/preps` |

## Backup Schedule

- **Automatic**: Daily at 3:00 AM (via cron)
- **Manual**: `./deployment/backup.sh`
- **Location**: `/home/ubuntu/dodo_bot_backups/`
- **Retention**: Last 7 backups

## Scheduled Jobs (Moscow Time)

| Job | Time | Description |
|-----|------|-------------|
| Shift notifications | Every 5 min | Check upcoming shifts |
| Prep notification | 08:55, 16:55 | Send prep lists to group |
| Who's working | 08:00 | Daily staff list |
| Feedback report | 22:50 | Daily feedback summary |
| Data cleanup | 00:00 | Reset daily data |

## Firewall Rules

```bash
# Allow web app (if needed externally)
sudo ufw allow 5001/tcp

# Check status
sudo ufw status
```

## Emergency Contacts

- Deployment Guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Maintenance Guide: [MAINTENANCE.md](MAINTENANCE.md)
- Bot logs: `/home/ubuntu/dodo_bot/logs/`
