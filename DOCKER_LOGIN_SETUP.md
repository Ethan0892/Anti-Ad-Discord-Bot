# Docker Login & Setup Guide

## First-Time Setup After Docker Deployment

After starting the bot with Docker for the first time, you need to create an owner account to access the Admin Portal.

### Step 1: Verify Containers Are Running

```bash
docker-compose ps

# Both should show "Up"
# anti-ad-bot    ... Up
# anti-ad-web    ... Up
```

### Step 2: Create Owner Account

Run the setup script inside the container:

```bash
docker-compose exec web-server python setup_web.py --owner
```

This will prompt you to:
1. Enter username (e.g., "admin" or your name)
2. Enter password (will not echo as you type)
3. Confirm password

**Example:**
```
$ docker-compose exec web-server python setup_web.py --owner
Creating owner account...
Username: ethan
Password: (enter password - won't show)
Confirm password: (enter again - won't show)
✓ Owner account created successfully!
```

### Step 3: Access the Admin Portal

Open your browser and go to:
- **Local:** http://localhost:5000
- **Remote:** http://bubblecraft.net:5000

### Step 4: Login

Use the credentials you just created:
- **Username:** (the one you entered in setup)
- **Password:** (the password you set)

---

## Troubleshooting

### "setup_web.py not found" error

**If you get:** `Error response from daemon: OCI runtime exec failed...`

The setup script might not exist in your version. Try:

```bash
# Check if file exists
docker-compose exec web-server ls -la setup_web.py

# If not found, create it manually
docker-compose exec web-server python -c "
import json
from pathlib import Path
from werkzeug.security import generate_password_hash

# Create user
username = input('Username: ')
password = input('Password: ')

users_file = Path('/app/users.json')
users = json.loads(users_file.read_text()) if users_file.exists() else {}

users[username] = {
    'password': generate_password_hash(password),
    'role': 'owner'
}

users_file.write_text(json.dumps(users, indent=2))
print('✓ Owner account created!')
"
```

### Can't Access Portal (Connection Refused)

1. **Check containers running:**
   ```bash
   docker-compose ps
   ```
   Should show web-server as "Up"

2. **Check web server logs:**
   ```bash
   docker-compose logs -f web-server
   ```
   Should show: `Running on http://0.0.0.0:5000`

3. **Check firewall:**
   ```bash
   sudo ufw allow 5000
   ```

4. **Test from container:**
   ```bash
   docker-compose exec web-server curl http://localhost:5000
   ```
   Should return HTML or JSON

### Forgot Password

To reset the password:

```bash
# Option 1: Recreate owner account
docker-compose exec web-server python setup_web.py --owner

# Option 2: Create a new account
docker-compose exec web-server python -c "
import json
from pathlib import Path
from werkzeug.security import generate_password_hash

username = input('New username: ')
password = input('New password: ')

users_file = Path('/app/users.json')
users = json.loads(users_file.read_text()) if users_file.exists() else {}

users[username] = {
    'password': generate_password_hash(password),
    'role': 'owner'
}

users_file.write_text(json.dumps(users, indent=2))
print(f'✓ Account {username} created!')
"
```

---

## After Login - First Steps

1. **Go to Training Images Tab**
   - Upload 3-5 spam images to train the bot
   - Formats: PNG, JPG, GIF, WEBP, BMP

2. **Go to Configuration Tab**
   - Review settings
   - Adjust similarity threshold if needed (0.75 is default)

3. **Go to Status Tab**
   - Verify bot shows as online
   - Check training image count

4. **Go to Profile Tab**
   - Change your password if desired
   - Verify your username/role

---

## Adding More Users

If you want to add team members with access:

1. **Login as owner**
2. **Go to Users tab** (only visible to owner/dev)
3. **Click "Add User"**
4. **Set username, password, role** (owner/dev/user)
5. **Share credentials with team member**

Or use command line:

```bash
docker-compose exec web-server python -c "
import json
from pathlib import Path
from werkzeug.security import generate_password_hash

# Get all users
users_file = Path('/app/users.json')
users = json.loads(users_file.read_text()) if users_file.exists() else {}

# Add new user
new_user = input('Username: ')
new_pass = input('Password: ')
new_role = input('Role (owner/dev/user): ')

users[new_user] = {
    'password': generate_password_hash(new_pass),
    'role': new_role
}

users_file.write_text(json.dumps(users, indent=2))
print(f'✓ User {new_user} created with role {new_role}')
"
```

---

## Default Configuration

After login, these are default settings (in Configuration tab):

- **DISCORD_TOKEN** - From your .env (masked as ***HIDDEN***)
- **GUILD_ID** - Your server ID (from .env)
- **SIMILARITY_THRESHOLD** - 0.75 (adjust 0.0-1.0)
- **PUNISHMENT_TYPE** - mute (mute/timeout/kick/ban)
- **MUTE_DURATION_DAYS** - 7
- **TIMEOUT_DURATION_MINUTES** - 60
- **AUTO_DELETE_IMAGE** - true
- **BOT_STATUS** - online
- **BOT_ACTIVITY_TEXT** - for spam images

---

## Quick Reference

```bash
# Create owner account
docker-compose exec web-server python setup_web.py --owner

# Access portal
# Browser: http://bubblecraft.net:5000

# Check logs
docker-compose logs -f web-server

# Restart containers
docker-compose restart

# View current users
docker-compose exec web-server cat users.json
```

---

**Ready to login!** 🎉

Once you've created your account and login works, check the Admin Portal tabs to get started:
- **Training Images** - Upload spam examples
- **Configuration** - Adjust bot settings
- **Profile** - Manage your account
- **Status** - Monitor bot health
