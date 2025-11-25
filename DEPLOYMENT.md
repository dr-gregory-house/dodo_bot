# Dodo Bot - Production Deployment Guide

Complete guide for deploying the Dodo Pizza Telegram Bot on Ubuntu 24 cloud server.

## Prerequisites

- **Server**: Ubuntu 24.04 LTS
- **Python**: Python 3.10 or higher
- **Sudo access**: Required for systemd service installation
- **Domain/IP**: Public access for web app (optional)

## Quick Start

### 1. Clone Repository

```bash
cd /home/ubuntu
git clone <your-repo-url> dodo_bot
cd dodo_bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment

Copy your `.env` file to the project root with the following variables:

```bash
BOT_TOKEN=your_telegram_bot_token
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
SPREADSHEET_ID=your_google_spreadsheet_id
GEMINI_API_KEY=your_gemini_api_key
```

Copy your Google Service Account JSON file:

```bash
cp /path/to/your/service_account.json /home/ubuntu/dodo_bot/
```

### 4. Create Required Directories

```bash
mkdir -p logs data
```

### 5. Install Systemd Services

```bash
# Copy service files to systemd directory
sudo cp deployment/dodo-bot.service /etc/systemd/system/
sudo cp deployment/dodo-webapp.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable dodo-bot
sudo systemctl enable dodo-webapp

# Start services
sudo systemctl start dodo-bot
sudo systemctl start dodo-webapp
```

### 6. Verify Installation

```bash
# Check bot status
sudo systemctl status dodo-bot

# Check web app status
sudo systemctl status dodo-webapp

# View bot logs
sudo journalctl -u dodo-bot -f

# View web app logs
sudo journalctl -u dodo-webapp -f

# Check health endpoint
curl http://localhost:5001/health
```

## Firewall Configuration

If you want to access the web app from outside:

```bash
# Allow web app port
sudo ufw allow 5001/tcp

# Check firewall status
sudo ufw status
```

## Setting Up Automatic Backups

Add to crontab for daily backups at 3 AM:

```bash
crontab -e
```

Add this line:

```
0 3 * * * /home/ubuntu/dodo_bot/deployment/backup.sh >> /home/ubuntu/dodo_bot/logs/backup.log 2>&1
```

## Directory Structure

```
/home/ubuntu/dodo_bot/
├── main.py                 # Main bot application
├── config.py              # Configuration loader
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── service_account.json   # Google credentials (not in git)
├── data/                  # JSON data files
├── logs/                  # Application logs
├── handlers/              # Bot command handlers
├── services/              # Business logic services
├── web_app/              # Flask web application
│   ├── app.py            # Web app entry point
│   └── templates/        # HTML templates
└── deployment/           # Deployment files
    ├── dodo-bot.service      # Bot systemd service
    ├── dodo-webapp.service   # Web app systemd service
    ├── start.sh              # Manual start script
    ├── backup.sh             # Backup script
    └── update.sh             # Update script
```

## Security Considerations

1. **File Permissions**: Ensure `.env` and `service_account.json` are only readable by the service user:
   ```bash
   chmod 600 .env service_account.json
   ```

2. **Service User**: Services run as `ubuntu` user by default. Consider creating a dedicated user:
   ```bash
   sudo useradd -r -s /bin/false dodobot
   ```

3. **Firewall**: Only expose necessary ports (5001 for web app if needed externally)

4. **HTTPS**: Consider setting up nginx reverse proxy with SSL for the web app

## Troubleshooting

See [MAINTENANCE.md](MAINTENANCE.md) for common issues and solutions.

## CI/CD Setup (GitHub Actions)

The project includes GitHub Actions workflows for Continuous Integration and Deployment.

### 1. Push to GitHub

```bash
git remote add origin https://github.com/yourusername/dodo_bot.git
git push -u origin main
```

### 2. Configure Secrets

Go to your GitHub Repository > Settings > Secrets and variables > Actions > New repository secret.

Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `HOST` | `87.239.106.209` | Your server IP address |
| `USERNAME` | `ubuntu` | SSH username |
| `SSH_KEY` | `-----BEGIN RSA PRIVATE KEY-----...` | Content of your `~/.ssh/ubuntu_dodo_bot.pem` |
| `BOT_TOKEN` | `123456:ABC...` | Your Telegram Bot Token |
| `SPREADSHEET_ID` | `1A2B3C...` | Your Google Spreadsheet ID |
| `GEMINI_API_KEY` | `AIza...` | Your Gemini API Key |
| `GOOGLE_CREDENTIALS` | `{ "type": "service_account"... }` | Content of `service_account.json` |

### 3. Workflow

- **CI**: Runs on every push. Checks code syntax and installs dependencies.
- **CD**: Runs on push to `main`. 
    1. Connects to server via SSH.
    2. **Injects secrets** into `.env` and `service_account.json`.
    3. Runs `./deployment/update.sh` to restart services.

## Next Steps

- Configure nginx reverse proxy for HTTPS (recommended for production)
- Set up monitoring with Prometheus/Grafana (optional)
- Configure log aggregation with ELK stack (optional)
- Set up automated alerts for service failures
