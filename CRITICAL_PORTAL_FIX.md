# CRITICAL FIX - Admin Portal Now Shows Configuration Panel

## The Issue
The admin portal wasn't showing the Server Configuration panel because:
- We added the new features to `index.html` (1300+ lines)
- But the web server was rendering `dashboard.html` (638 lines, outdated)

## The Fix ✅
Changed `web_server.py` to render `index.html` instead of `dashboard.html`

## Deploy to Production

SSH to your production server and run:

```bash
cd /opt/Anti-Ad-Discord-Bot
git pull origin main
docker-compose down
docker-compose up -d --build
```

Then visit: `http://bubblecraft.net:5000` and hard refresh: **Ctrl + Shift + R**

---

## What You'll Now See

**Server Configuration Panel** with three sections:

### 1. Detection Settings
- Toggle: Enable Spam Detection
- Slider: Similarity Threshold (0.5-0.95)
- Toggle: Auto-delete Images
- Button: Save

### 2. Notification Settings
- Toggle: Send Global Notifications
- Input: Notification Cooldown (minutes)
- Input: Mute Duration (days)
- Button: Save

### 3. Channel Management
- Whitelist channels
- Blacklist channels
- Remove buttons for each

---

## Verification

```bash
# Check the deployed commit
docker exec anti-ad-web git log --oneline -1
# Should show: 4f25473 Fix admin portal to use index.html instead of dashboard.html

# Verify index.html is being served
docker exec anti-ad-web grep "Server Configuration" /app/templates/dashboard.html 2>/dev/null
# Should return nothing (because we're now using index.html)

# Verify index.html has the content
docker exec anti-ad-web grep -c "Server Configuration" /app/templates/index.html
# Should show: 2
```

---

**Portal should now display all new features!** 🎉
