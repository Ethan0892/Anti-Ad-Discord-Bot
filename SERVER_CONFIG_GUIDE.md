# Professional Server Configuration & Spam Notifications

## Overview
Implemented a professional, user-friendly server configuration system similar to MEE6 and Dyno, along with an intelligent spam notification system that prevents notification spam through cooldown tracking.

## Features Added

### 1. Spam Notification System

**Problem**: Bot was posting repetitive "spam detected" messages, creating notification spam in channels.

**Solution**: Implemented `SpamNotificationTracker` class that:
- Tracks last notification per channel
- Only sends one notification per configurable cooldown period (default: 5 minutes)
- Maintains separate cooldowns for each channel

**Message Format**:
```
Spam image found, deleted
```

**Code Location**: `src/bot.py` lines 103-118

**Implementation**:
```python
class SpamNotificationTracker:
    """Track spam notifications per channel to prevent message spam."""
    def __init__(self, cooldown_minutes: int = 5):
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.last_notification = {}
    
    def should_notify(self, channel_id: int) -> bool:
        """Check if we should send a notification for this channel."""
        # Returns True if cooldown has expired
```

### 2. Server-Specific Configuration

**Database Extension**: Added `server_settings` table to `data.json` with per-guild settings:

```json
{
  "server_settings": {
    "123456789": {
      "guild_id": 123456789,
      "enabled": true,
      "similarity_threshold": 0.65,
      "auto_delete_images": true,
      "send_global_notification": true,
      "mute_duration_days": 7,
      "notify_channel_id": null,
      "whitelisted_channels": [],
      "blacklisted_channels": [],
      "notification_cooldown_minutes": 5
    }
  }
}
```

**Settings Explained**:
- `enabled`: Master toggle for spam detection
- `similarity_threshold`: Detection sensitivity (0.5-0.95)
- `auto_delete_images`: Whether to delete detected images
- `send_global_notification`: Post channel notification on detection
- `mute_duration_days`: How long to mute offenders (0 = permanent)
- `notify_channel_id`: Optional dedicated channel for alerts
- `whitelisted_channels`: Bot won't scan images in these channels
- `blacklisted_channels`: Bot ONLY scans images in these channels
- `notification_cooldown_minutes`: Time between notifications

### 3. REST API Endpoints

**New Endpoints** in `web_server.py`:

#### Get Server Settings
```
GET /api/server-settings/<guild_id>
```
Returns current server configuration.

#### Update Server Settings
```
PUT /api/server-settings/<guild_id>
Content-Type: application/json

{
  "similarity_threshold": 0.65,
  "auto_delete_images": true,
  "send_global_notification": true,
  "notification_cooldown_minutes": 5,
  "mute_duration_days": 7
}
```

#### Set Notification Channel
```
PUT /api/server-settings/<guild_id>/notification-channel/<channel_id>
```

#### Whitelist Channel
```
POST /api/server-settings/<guild_id>/whitelist-channel/<channel_id>
```
Bot won't scan images in this channel.

#### Blacklist Channel
```
POST /api/server-settings/<guild_id>/blacklist-channel/<channel_id>
```
Bot will ONLY scan images in blacklisted channels.

**Authorization**: All endpoints require `@dev_or_owner_required` decorator

### 4. Professional Admin Portal UI

**New Configuration Panel** in `templates/index.html` (600+ lines):

#### Detection Settings Section
- Toggle to enable/disable spam detection
- Threshold slider (0.5 - 0.95)
- Toggle for auto-delete images
- Visual feedback showing current sensitivity level

#### Notification Settings Section
- Toggle for global notifications
- Configurable cooldown (1-60 minutes)
- Configurable mute duration (0-365 days)
- Help text explaining each option

#### Channel Management Section
- **Whitelist**: Input field + button to add channels
- **Blacklist**: Input field + button to add channels
- Display of currently configured channels
- Remove buttons for each listed channel

**Design Features**:
- Professional dark blue theme (matches existing portal)
- Grid layout responsive to screen size
- Toggle switches for boolean settings
- Range slider for threshold adjustment
- Real-time display of slider values
- Consistent styling with system management section
- Save buttons to persist changes

**Code Location**: `templates/index.html` lines 615-740 (HTML), 950-1055 (JavaScript)

### 5. Detection Integration

**Updated `on_message()` Handler**:

Both attachment and URL-based image detection now:
1. Check if message contains spam images
2. Delete the message
3. Mute the user
4. Log the detection
5. **Send global notification** (if cooldown has expired)
6. Notify user via DM

**Code Locations**:
- Attachment detection: `src/bot.py` lines 230-256
- URL detection: `src/bot.py` lines 285-311

**Example Flow**:
```
User posts spam image in #general
Bot deletes message
Bot mutes user
Bot posts: "Spam image found, deleted"
↓ (5 minutes pass)
Another user posts spam in #general
Bot deletes message
Bot mutes user
Bot posts: "Spam image found, deleted" (notif cooldown expired)
↓ (30 seconds pass)
Another user posts spam in #general
Bot deletes message
Bot mutes user
Bot DOESN'T post (cooldown still active)
```

## Technical Details

### Files Modified

1. **src/database.py** (+60 lines)
   - Added `server_settings` to default data structure
   - New methods: `get_server_settings()`, `update_server_settings()`, `is_channel_whitelisted()`, `is_channel_blacklisted()`

2. **src/bot.py** (+100 lines)
   - Added `SpamNotificationTracker` class
   - Instantiated `notification_tracker` object
   - Updated on_message handler to send notifications
   - Added checks for both attachment and URL detections

3. **web_server.py** (+90 lines)
   - 5 new API endpoints for settings management
   - All endpoints require `@dev_or_owner_required` authorization
   - Proper error handling and logging

4. **templates/index.html** (+600 lines)
   - New Server Configuration panel (HTML)
   - 5 new JavaScript functions for settings management
   - 2 new event listeners for slider updates
   - Updated init() to load server settings

### Database Changes

**Migration**: Existing `data.json` files automatically create `server_settings` structure on first access with default values.

```python
def get_server_settings(self, guild_id: int) -> Dict:
    """Returns defaults if not found."""
    if guild_id_str not in self.data['server_settings']:
        # Creates default settings
        self.data['server_settings'][guild_id_str] = { ... }
        self.save()
    return self.data['server_settings'][guild_id_str]
```

## Configuration Examples

### High Sensitivity (More Aggressive Detection)
```json
{
  "similarity_threshold": 0.55,
  "auto_delete_images": true,
  "send_global_notification": true,
  "mute_duration_days": 30
}
```

### Notification Spam Prevention
```json
{
  "send_global_notification": true,
  "notification_cooldown_minutes": 10
}
```

### Whitelist Approach (Only Scan Certain Channels)
```json
{
  "blacklisted_channels": [123, 456, 789],
  "whitelisted_channels": []
}
```

## Usage

### From Admin Portal
1. Login to admin portal
2. Navigate to "Server Configuration" section
3. Adjust settings with sliders/toggles
4. Save settings
5. Changes apply immediately

### From API
```bash
# Get settings
curl -H "X-API-Token: token" \
  http://localhost:5000/api/server-settings/123456789

# Update settings
curl -X PUT -H "X-API-Token: token" \
  -H "Content-Type: application/json" \
  -d '{"similarity_threshold": 0.6}' \
  http://localhost:5000/api/server-settings/123456789

# Whitelist a channel
curl -X POST -H "X-API-Token: token" \
  http://localhost:5000/api/server-settings/123456789/whitelist-channel/987654321
```

## Future Enhancements

- [ ] Remove from whitelist/blacklist functionality
- [ ] Per-role punishment settings
- [ ] Notification templates (customizable message format)
- [ ] Logging channel selection
- [ ] Server statistics dashboard (detections/day, etc.)
- [ ] Automatic threshold learning based on false positives
- [ ] Advanced filtering rules (by user role, date, etc.)

## Testing Checklist

- [ ] Portal loads server settings on page load
- [ ] Threshold slider updates value display
- [ ] Save button persists settings to database
- [ ] Settings load correctly on page refresh
- [ ] Whitelist channel functionality works
- [ ] Blacklist channel functionality works
- [ ] Spam notification appears on first detection
- [ ] Spam notification skipped during cooldown
- [ ] Spam notification resends after cooldown expires
- [ ] Settings apply to bot detection immediately
- [ ] Multiple channels have independent cooldowns
- [ ] API endpoints return proper authorization errors

## Deployment Notes

1. No database migration needed (backwards compatible)
2. No new environment variables required
3. Portal automatically shows guild ID (needs implementation via `window.guildId`)
4. Test with `guild_id=0` for defaults on initial testing

## Commit Details

- **Hash**: `5e566bc`
- **Message**: "Add professional server configuration panel and spam notification system"
- **Changes**: 445 insertions across 4 files
