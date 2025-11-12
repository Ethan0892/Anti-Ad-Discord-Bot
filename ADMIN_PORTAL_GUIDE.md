# Admin Portal - System Management Guide

Professional admin control panel with full system management capabilities.

---

## System Management Panel Overview

The System Management panel provides administrators with comprehensive control over the Anti-Ad Bot deployment, including updates, restarts, and training data synchronization.

### Access Requirements

- **Owner Role** - Full access to all system management features
- **Dev Role** - Full access to all system management features
- **User Role** - No access to system management

---

## Features

### 1. Application Updates

**Check for Updates**
- Queries GitHub repository for newer versions
- Shows current version status
- Displays available commits and changes
- Takes 5-10 seconds typically

**When Updates Are Available:**
- Status indicator changes to "Updates Available"
- "Pull Updates" button becomes enabled
- Shows detailed update information

**Pull Updates**
- Downloads latest code from GitHub (main branch)
- Configuration files preserved automatically
- Training data folder preserved
- Takes 10-30 seconds depending on connection
- Requires service restart to apply

**Update Process:**
1. Click "Check for Updates"
2. Review available updates
3. Click "Pull Updates" if available
4. Review output for any errors
5. Click "Restart Bot and Web Server" to apply

**What Gets Updated:**
- Bot code and algorithms
- Web server and API
- Detection engine improvements
- Bug fixes

**What Is NOT Updated:**
- Your configuration settings
- Training images
- User data
- Logs

---

### 2. Service Management

**Restart Bot and Web Server**
- Restarts both Discord bot and web interface
- Configuration changes applied
- Takes 10-15 seconds

**When to Restart:**
- After pulling updates
- After configuration changes (optional, usually automatic)
- If bot is unresponsive
- After pulling new training data

**Warning:**
- Service will be offline 10-15 seconds
- Discord bot will disconnect temporarily
- Web portal will be unavailable
- Active connections will be dropped
- Automatic reconnect after restart

**Restart Process:**
1. Confirm restart action
2. Service becomes unavailable (shown in status)
3. Wait 10-15 seconds
4. Service comes back online automatically
5. Refresh page if needed

**What Happens During Restart:**
- Both services gracefully shut down
- Unsaved data is flushed to disk
- Services start fresh with current configuration
- Database and training data preserved

---

### 3. Training Data Synchronization

**Sync Training Data from GitHub**
- Pulls latest training images from GitHub repository
- New images immediately available for detection
- Useful for shared training data across servers
- Takes 5-30 seconds depending on size

**How Synchronization Works:**
1. Connects to GitHub repository
2. Fetches latest Training-Data directory
3. Downloads new/updated images
4. Validates image formats
5. Makes images available to detector

**When to Sync:**
- After adding images to GitHub repository
- When another admin adds training data
- To pull community-curated spam examples
- For regular training data updates

**Sync Output Shows:**
- Total images synced
- Operation status
- Any errors encountered
- Final image count

---

## System Status Indicator

Located in header with three states:

**Up to Date** (Green)
- All code is current
- No updates available
- System optimal

**Updates Available** (Yellow)
- GitHub has newer version
- Pull updates recommended
- Check output for details

**Error** (Red)
- Update check failed
- GitHub connection issue
- Review error message

---

## Output Logs

Each operation shows real-time output in collapsible sections:

**Update Output:**
- Git pull status
- New commits pulled
- Merge conflicts (if any)
- Completion status

**Restart Output:**
- Shutdown messages
- Service initialization
- Startup logs
- Status confirmation

**Sync Output:**
- Git fetch status
- Image count
- Download progress
- Sync completion

**To View Full Output:**
- Scroll in output box
- Output auto-expands to fit content
- Maximum height: 150px (scrollable)
- Monospace font for clarity

---

## Common Operations

### Update to Latest Version

```
1. Click "Check for Updates"
   - Wait for check to complete
   - Review status

2. If updates available:
   - Click "Pull Updates"
   - Wait for pull to complete
   - Review output for errors

3. Click "Restart Bot and Web Server"
   - Confirm the action
   - Wait 10-15 seconds
   - Verify status returns to "Online"
```

**Total Time:** 30-60 seconds

### Sync New Training Images

```
1. Add images to GitHub repository
   - Push to main branch
   - Commit messages optional

2. In Admin Portal:
   - Click "Sync Training Data from GitHub"
   - Wait for sync to complete
   - Review image count

3. New images immediately available
   - No restart needed
   - Bot will use them for next detection
```

**Total Time:** 5-30 seconds

### Handle Unresponsive Bot

```
1. Check bot status
   - Should show "Online" or "Offline"

2. If offline:
   - Click "Restart Bot and Web Server"
   - Wait 10-15 seconds
   - Verify status changes to "Online"

3. If still offline:
   - Check Docker container: docker-compose logs
   - Verify no disk space issues
   - Check network connectivity
```

---

## Error Handling

### Update Check Fails

**Possible Causes:**
- No internet connection
- GitHub API rate limited
- GitHub is down
- Repository not accessible

**Solutions:**
- Check network connectivity
- Wait 5 minutes and retry
- Verify GitHub repository URL
- Check firewall/proxy settings

### Update Pull Fails

**Possible Causes:**
- Local changes conflict with GitHub
- Network interruption
- Insufficient disk space
- Git configuration issue

**Solutions:**
- Check git status: `git status`
- Review error output
- Verify disk space available
- Restart and retry

### Restart Doesn't Work

**Possible Causes:**
- Service hung/frozen
- Port already in use
- Insufficient permissions
- Docker issues

**Solutions:**
- Manual restart: `docker-compose restart`
- Force stop: `docker-compose down`
- Check logs: `docker-compose logs`
- Verify Docker running

### Sync Training Data Fails

**Possible Causes:**
- GitHub connection issue
- Training-Data folder permission
- Git not initialized
- Corrupted image files

**Solutions:**
- Check GitHub connectivity
- Verify folder permissions
- Manual sync: `git pull origin main`
- Validate image files

---

## Best Practices

1. **Before Updates**
   - Check current status
   - Review changes in output
   - Plan for 10-15 second downtime

2. **Regular Maintenance**
   - Check for updates weekly
   - Sync training data regularly
   - Monitor system logs

3. **During Peak Hours**
   - Avoid restarts when users active
   - Schedule updates during off-hours
   - Notify users before restarts

4. **Training Data**
   - Keep GitHub repository updated
   - Document spam examples
   - Sync regularly for consistency
   - Review image quality

---

## Security Notes

- Owner and dev roles can restart services
- Owner and dev roles can pull updates
- All operations logged with username/timestamp
- API token required for all operations
- Changes require re-authentication

---

## Troubleshooting

### Service Offline After Restart

**Wait 15 seconds** - Services take time to fully boot

**If Still Offline:**
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs anti-ad-bot

# Manual restart
docker-compose restart
```

### Updates Won't Apply

**Solution:**
```bash
# Restart service explicitly
docker-compose down
docker-compose pull
docker-compose up -d
```

### Training Data Not Updating

**Solutions:**
1. Verify images pushed to GitHub
2. Check GitHub branch (should be main)
3. Verify SSH keys configured
4. Manual sync: `git pull origin main` in Training-Data/

### Status Checker Shows "Offline"

**Causes:**
- Web server not running
- Port blocked
- Process crashed

**Fix:**
```bash
# Restart web server
docker-compose restart anti-ad-web

# Or full restart
docker-compose restart
```

---

## Configuration Files

System Management interacts with:

- `web_server.py` - API endpoints for updates/restart
- `config/.env` - Configuration storage
- `config/config.py` - Active configuration
- `.git/` - Version control
- `Training-Data/` - Training images

**These are NOT edited by System Management:**
- User database (users.json)
- Detection logs
- Application source code (except git pull)
- Bot token or secrets

---

## Advanced: Manual Operations

**Check for Updates (Command Line):**
```bash
cd /path/to/Anti-Ad
git fetch origin main
git log --oneline main ^HEAD | head -10
```

**Pull Updates (Command Line):**
```bash
cd /path/to/Anti-Ad
git pull origin main --ff-only
```

**Restart Services (Command Line):**
```bash
# Graceful restart
docker-compose restart

# Force restart
docker-compose down && docker-compose up -d
```

**Sync Training Data (Command Line):**
```bash
cd /path/to/Anti-Ad
git pull origin main --ff-only
```

---

## Support

For issues with System Management:

1. Check error output displayed in portal
2. Review logs: `docker-compose logs`
3. Try manual operations via command line
4. Open GitHub issue with error details

Error messages are logged with:
- Timestamp
- Operation attempted
- User who performed action
- Full error text

---

**Last Updated:** November 2025
**Portal Version:** 2.0
**Minimum Bot Version:** 2.0
