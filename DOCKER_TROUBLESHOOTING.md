# Docker Troubleshooting Guide

## Web Server Not Accessible

### Problem
Cannot access the Admin Portal at `http://localhost:5000` or `http://bubblecraft.net:5000`

### Solution Checklist

#### 1. Verify Containers Are Running
```bash
docker-compose ps
```

Expected output:
```
NAME              COMMAND                  SERVICE        STATUS
anti-ad-bot       "python src/bot.py"      anti-ad-bot    Up
anti-ad-web       "python web_server.py"   web-server     Up
```

If either shows "Exit" or "Exited", check logs:
```bash
docker-compose logs -f web-server
docker-compose logs -f anti-ad-bot
```

#### 2. Check Web Server Logs
```bash
docker-compose logs -f web-server
```

Look for:
- Python errors or exceptions
- Port binding issues
- Module import failures

#### 3. Test Connectivity from Container
```bash
docker-compose exec web-server curl -v http://localhost:5000/api/status
```

This will test if the web server is actually listening inside the container.

#### 4. Verify Port Mapping
```bash
docker port anti-ad-web
```

Should output:
```
5000/tcp -> 0.0.0.0:5000
```

If not, the port isn't properly exposed.

#### 5. Check Firewall (Port 5000)

**Linux (UFW):**
```bash
# Allow port 5000
sudo ufw allow 5000

# Check status
sudo ufw status

# Check what's using the port
sudo netstat -tlnp | grep 5000
```

**Windows/Mac:**
- Check firewall settings for port 5000
- Windows Defender may block new apps

#### 6. Port Already in Use
```bash
# Linux/Mac - find process using port 5000
sudo lsof -i :5000

# Windows
netstat -ano | findstr :5000
```

**Solution:** Change port in `docker-compose.yml`:
```yaml
web-server:
  ports:
    - "5001:5000"  # Access at http://localhost:5001
```

Then restart:
```bash
docker-compose restart
```

---

## Containers Keep Restarting

### Problem
Containers start but immediately restart or exit with errors

### Solution

1. **View the error logs:**
   ```bash
   docker-compose logs -f
   ```

2. **Common issues:**
   - Missing `DISCORD_TOKEN` in `config/.env`
   - Invalid environment variables
   - Python module not found
   - File/volume mounting issues

3. **Check environment:**
   ```bash
   cat config/.env
   # Verify DISCORD_TOKEN and other variables are set
   ```

4. **Restart with fresh logs:**
   ```bash
   docker-compose down
   docker-compose up
   # (without -d to see logs in real-time)
   ```

---

## Environment Variables Not Set

### Problem
Warnings like:
```
WARN[0000] The "DISCORD_TOKEN" variable is not set. Defaulting to a blank string.
WARN[0000] The "GUILD_ID" variable is not set. Defaulting to a blank string.
```

### Solution

1. **Create config/.env from example:**
   ```bash
   cp config/.env.example config/.env
   ```

2. **Edit and add your values:**
   ```bash
   nano config/.env  # or your preferred editor
   ```

   Required variables:
   ```ini
   DISCORD_TOKEN=your_bot_token_here
   GUILD_ID=your_guild_id_here
   MUTED_ROLE_ID=your_role_id_here
   APPEAL_CHANNEL_ID=your_channel_id_here
   LOG_CHANNEL_ID=your_log_channel_id_here
   WEB_API_TOKEN=change-this-secure-token
   ```

3. **Restart containers:**
   ```bash
   docker-compose restart
   ```

4. **Verify variables loaded:**
   ```bash
   docker-compose exec web-server env | grep DISCORD_TOKEN
   # Should show your token, not blank
   ```

---

## Remote Access (bubblecraft.net:5000)

### Problem
Can access locally but not from external machine

### Solution

1. **Verify port is exposed to all interfaces:**
   ```bash
   docker port anti-ad-web
   # Should show: 5000/tcp -> 0.0.0.0:5000
   ```

2. **Check firewall allows external traffic:**
   ```bash
   # Linux UFW
   sudo ufw allow from any to any port 5000
   
   # Or more restrictively
   sudo ufw allow from 192.168.1.100 to any port 5000
   ```

3. **Test from another machine:**
   ```bash
   curl http://YOUR_SERVER_IP:5000/api/status
   
   # Or with DNS
   curl http://bubblecraft.net:5000/api/status
   ```

4. **If behind Nginx reverse proxy:**
   ```nginx
   location /bot {
       proxy_pass http://localhost:5000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
   }
   ```

   Then access at: `http://bubblecraft.net/bot`

5. **Verify containers are running:**
   ```bash
   docker-compose ps
   docker-compose logs -f web-server
   ```

---

## Docker Commands Reference

### Container Management
```bash
# Start services (background)
docker-compose up -d

# Start and view logs
docker-compose up

# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Restart all
docker-compose restart

# Restart specific service
docker-compose restart web-server

# Rebuild images (after code changes)
docker-compose up -d --build

# Force rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

### Viewing Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web-server
docker-compose logs -f anti-ad-bot

# Last 50 lines only
docker-compose logs --tail=50

# Without timestamps
docker-compose logs -f --no-log-prefix
```

### Debugging
```bash
# Execute command in container
docker-compose exec web-server python --version

# Run Python code
docker-compose exec web-server python -c "from src import bot; print('OK')"

# Check environment
docker-compose exec web-server env | sort

# View files in container
docker-compose exec web-server ls -la

# Monitor resource usage
docker stats

# Check network
docker network ls
docker network inspect anti-ad-discord-bot_bot-network
```

### Data Management
```bash
# View data volumes
docker volume ls

# Backup data
docker-compose exec web-server cat data.json > data_backup.json

# Remove everything (keeps .env and Training-Data)
docker-compose down

# Remove everything including data (CAREFUL!)
docker-compose down -v
```

---

## Useful Diagnostic Checklist

- [ ] Run `docker-compose ps` - all containers "Up"?
- [ ] Run `docker-compose logs -f web-server` - any errors?
- [ ] Run `docker-compose exec web-server curl localhost:5000` - web server responding?
- [ ] Run `cat config/.env` - all values set (not blank)?
- [ ] Run `docker port anti-ad-web` - port mapped correctly?
- [ ] Run `sudo netstat -tlnp | grep 5000` - port listening?
- [ ] Run `sudo ufw status` - firewall allows port 5000?
- [ ] Try accessing from another machine - network accessible?

---

## Need More Help?

Check these files for more information:
- **README.md** - Main documentation
- **LINUX_DEPLOYMENT.md** - Linux-specific setup
- **SECURITY.md** - Security best practices
- **docker-compose.yml** - Service configuration

Container logs are your best friend:
```bash
docker-compose logs -f
```

If stuck, save logs and review carefully:
```bash
docker-compose logs > debug_logs.txt
cat debug_logs.txt
```
