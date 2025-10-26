# Anti-Ad Bot - Linux Deployment Guide

Complete guide for deploying Anti-Ad Bot on Linux servers.

## Quick Start (Ubuntu/Debian)

### 1. Install Dependencies

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and required packages
sudo apt-get install -y python3 python3-pip python3-venv

# Install OpenCV dependencies
sudo apt-get install -y libopencv-dev python3-opencv

# Optional: Install screen for background execution
sudo apt-get install -y screen
```

### 2. Clone and Setup

```bash
# Clone the project
git clone https://github.com/Ethan0892/Anti-Ad-Discord-Bot.git
cd Anti-Ad-Discord-Bot

# Make startup script executable
chmod +x START.sh

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure

```bash
# Copy configuration template
cp config/.env.example config/.env

# Edit with your Discord token and IDs
nano config/.env
```

### 4. Run

```bash
# Start bot and portal
./START.sh

# Or just the bot
./START.sh --bot-only

# Or just the portal
./START.sh --portal-only
```

## Production Deployment with Systemd

### Setup User Account

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash botuser

# Switch to user
sudo su - botuser

# Clone project
git clone https://github.com/Ethan0892/Anti-Ad-Discord-Bot.git
cd Anti-Ad-Discord-Bot

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp config/.env.example config/.env
nano config/.env

# Exit back to root
exit
```

### Install Systemd Services

```bash
# Copy service files
sudo cp Anti-Ad-Discord-Bot/anti-ad-bot.service /etc/systemd/system/
sudo cp Anti-Ad-Discord-Bot/anti-ad-portal.service /etc/systemd/system/

# Update paths in service files (replace with actual paths)
sudo nano /etc/systemd/system/anti-ad-bot.service
sudo nano /etc/systemd/system/anti-ad-portal.service

# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable anti-ad-bot.service
sudo systemctl enable anti-ad-portal.service

# Start services
sudo systemctl start anti-ad-bot.service
sudo systemctl start anti-ad-portal.service

# Check status
sudo systemctl status anti-ad-bot.service
sudo systemctl status anti-ad-portal.service
```

### View Logs

```bash
# Bot logs
sudo journalctl -u anti-ad-bot.service -f

# Portal logs
sudo journalctl -u anti-ad-portal.service -f

# Both
sudo journalctl -u anti-ad-bot.service -u anti-ad-portal.service -f
```

### Manage Services

```bash
# Start
sudo systemctl start anti-ad-bot.service

# Stop
sudo systemctl stop anti-ad-bot.service

# Restart
sudo systemctl restart anti-ad-bot.service

# Check status
sudo systemctl status anti-ad-bot.service

# Disable from startup
sudo systemctl disable anti-ad-bot.service
```

## Docker Deployment

### Using Docker Compose

```bash
cd Anti-Ad-Discord-Bot

# Create .env
cp config/.env.example .env
nano .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Using Docker Only

```bash
# Build image
docker build -t anti-ad-bot:latest .

# Run bot
docker run -d \
  --name anti-ad-bot \
  -e DISCORD_TOKEN=your_token \
  -e GUILD_ID=your_guild_id \
  -e MUTED_ROLE_ID=your_role_id \
  -e APPEAL_CHANNEL_ID=your_channel_id \
  -e LOG_CHANNEL_ID=your_channel_id \
  -v $(pwd)/Training-Data:/app/Training-Data \
  -v $(pwd)/data.json:/app/data.json \
  anti-ad-bot:latest
```

## Reverse Proxy Setup (Nginx)

### Install Nginx

```bash
sudo apt-get install -y nginx

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Configure Nginx

Create `/etc/nginx/sites-available/anti-ad`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/anti-ad /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your-domain.com

# Update nginx config to use SSL
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

## Firewall Configuration

### UFW (Ubuntu Firewall)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### iptables

```bash
# Allow port 5000 (Admin Portal)
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT

# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Save rules
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

## Monitoring and Maintenance

### Check Resources

```bash
# CPU and memory usage
top -p $(pgrep -f "python3 src/bot.py")

# Disk space
df -h

# Logs size
du -sh logs/
```

### Rotate Logs

Create `/etc/logrotate.d/anti-ad-bot`:

```
/home/botuser/Anti-Ad-Discord-Bot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 botuser botuser
    sharedscripts
}
```

### Backup Strategy

```bash
# Backup training data and user data
sudo su - botuser
tar -czf backup-$(date +%Y%m%d).tar.gz Training-Data/ data.json config/.env

# Move to backup location
mv backup-*.tar.gz /home/backups/
```

## Troubleshooting

### Bot Won't Start

```bash
# Check logs
sudo journalctl -u anti-ad-bot.service -n 50

# Verify .env exists
cat config/.env | grep DISCORD_TOKEN

# Check Python version
python3 --version

# Test imports
python3 -c "import discord; print('Discord OK')"
```

### Portal Not Accessible

```bash
# Check if running
curl http://localhost:5000

# Check firewall
sudo ufw status

# Check Nginx (if using)
sudo systemctl status nginx
sudo nginx -t
```

### High Memory Usage

```bash
# Reduce cache
# Edit config/.env:
SIMILARITY_THRESHOLD=0.8  # Increase threshold

# Limit training data to 5-10 images
# Remove old images from Training-Data/

# Restart services
sudo systemctl restart anti-ad-bot
```

## Performance Tuning

### Bot Performance

```bash
# config/.env
# Increase threshold for faster detection
SIMILARITY_THRESHOLD=0.8

# Disable unused logging
LOG_APPEALS=false

# Limit detection cache
```

### System Performance

```bash
# Increase file descriptors
ulimit -n 65536

# Enable swap (if needed)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Support

For issues specific to Linux deployment, check:
- Service logs: `sudo journalctl -u anti-ad-bot.service -f`
- Python dependencies: `pip list`
- Discord token validity
- Firewall settings
- File permissions

See main README.md for general troubleshooting.
