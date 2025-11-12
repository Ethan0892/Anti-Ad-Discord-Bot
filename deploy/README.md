# Deployment Assets

This directory contains service unit files and deployment notes for the Anti-Ad Discord Bot and its admin portal.

## Files
- `anti-ad-bot.service` — systemd unit for the Discord bot process.
- `anti-ad-portal.service` — systemd unit for the Flask admin portal.

## Install / Update Units
```bash
sudo cp deploy/anti-ad-bot.service /etc/systemd/system/anti-ad-bot.service
sudo cp deploy/anti-ad-portal.service /etc/systemd/system/anti-ad-portal.service
sudo systemctl daemon-reload
sudo systemctl enable anti-ad-bot anti-ad-portal
sudo systemctl restart anti-ad-bot anti-ad-portal
```

## Logs
Both units use `StandardOutput=journal`. View logs:
```bash
journalctl -u anti-ad-bot -f
journalctl -u anti-ad-portal -f
```

## Update Sequence
1. Pull latest code: `git pull origin main`
2. Update Python deps: `source venv/bin/activate && pip install -r requirements.txt`
3. Restart services.

## Health Check
Use the portal `/api/status` and `/api/system/info` endpoints to verify bot online status and metrics.
