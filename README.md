# Dodo Pizza Telegram Bot

Production-ready Telegram bot for managing Dodo Pizza operations including schedules, preparations, medical records, and employee management.

## Features

- 📅 **Schedule Management**: View employee shifts and working hours
- 📝 **Preparation Lists**: Daily and shift-based preparation tracking
- 🏥 **Medical Records**: Track medical commissions and sanitary minimums
- 💬 **Group Notifications**: Automated prep lists and shift reminders
- 📊 **Ratings System**: Store and display ratings with photos
- 🍽️ **Worker Instructions**: Step-by-step guides for staff
- 🌐 **Web Interface**: Tablet-friendly web app for viewing prep lists
- 💰 **Wages Calculator**: Employee earnings tracking
- 🍕 **Defrost Management**: Track freezer inventory and defrosting items

## Quick Start

### Prerequisites

- Ubuntu 24.04 LTS
- Python 3.10+
- Telegram Bot Token
- Google Sheets API credentials
- Gemini API key

### Installation

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

Quick local setup:

```bash
# Clone repository
git clone <your-repo> dodo_bot
cd dodo_bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Edit with your credentials
cp /path/to/service_account.json .

# Run bot
python main.py
```

### Production Deployment

For production deployment on Ubuntu 24:

```bash
./deployment/setup.sh
```

This will:
- Install system dependencies
- Set up virtual environment
- Install Python packages
- Configure systemd services
- Set up automatic backups

## Architecture

```
dodo_bot/
├── main.py              # Bot entry point
├── config.py            # Configuration
├── handlers/            # Command handlers
│   ├── start.py        # Registration & start
│   ├── menu.py         # Main menu
│   ├── preps.py        # Preparations
│   ├── schedule.py     # Shift schedules
│   ├── medical.py      # Medical records
│   └── ...
├── services/            # Business logic
│   ├── sheets.py       # Google Sheets integration
│   ├── scheduler.py    # Notification scheduler
│   └── ...
├── web_app/            # Flask web application
│   ├── app.py
│   └── templates/
└── deployment/         # Production files
    ├── *.service       # Systemd services
    └── *.sh            # Management scripts
```

## Configuration

Environment variables in `.env`:

```bash
BOT_TOKEN=your_telegram_bot_token
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
SPREADSHEET_ID=your_google_spreadsheet_id
GEMINI_API_KEY=your_gemini_api_key
```

## Services

### Telegram Bot
- Port: N/A (polling mode)
- Service: `dodo-bot.service`
- Logs: `/home/ubuntu/dodo_bot/logs/dodo_bot.log`

### Web Application
- Port: 5001
- Service: `dodo-webapp.service`
- Logs: `/home/ubuntu/dodo_bot/logs/webapp.log`
- Health check: `http://localhost:5001/health`

## Management

See [MAINTENANCE.md](MAINTENANCE.md) for detailed operational procedures.

### Common Commands

```bash
# Start services
sudo systemctl start dodo-bot dodo-webapp

# Stop services
sudo systemctl stop dodo-bot dodo-webapp

# Restart services
sudo systemctl restart dodo-bot dodo-webapp

# View logs
sudo journalctl -u dodo-bot -f

# Update bot
./deployment/update.sh

# Create backup
./deployment/backup.sh
```

## Features in Detail

### Automated Notifications
- **Shift Reminders**: 1 hour before shift start
- **Prep Lists**: 8:55 AM and 4:55 PM Moscow time
- **Who's Working**: 8:00 AM daily
- **Feedback Summary**: 10:50 PM daily

### Medical Tracking
- Track medical commission dates
- Sanitary minimum expiration alerts
- Role-based employee categorization
- Expiring document notifications

### Preparation Management
- Daily and shift-based prep items
- Morning and evening configurations
- Weekday-specific requirements
- Real-time Google Sheets integration

## Development

To run in development mode:

```bash
source venv/bin/activate
python main.py
```

Web app development:

```bash
cd web_app
python app.py
```

## Security

- Environment variables for sensitive data
- Service account authentication for Google Sheets
- Systemd security hardening
- Log rotation to prevent disk overflow
- Regular automated backups

## Monitoring

- Health check endpoint: `/health`
- Systemd service status
- Application logs with rotation
- Separate error logs
- Resource usage limits

## License

[Your License]

## Support

For issues and questions, see [MAINTENANCE.md](MAINTENANCE.md) troubleshooting section.
