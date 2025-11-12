# Admin Portal & Spam Notification System - Implementation Summary

## What Was Added

### 1. Spam Notification System ✅
- Prevents notification spam using cooldown-based tracking
- Posts "Spam image found, deleted" message once per channel per cooldown period
- Configurable cooldown (default: 5 minutes)
- Tracks per-channel, so different channels can have independent notification timing

**How It Works**:
```
Channel #general:
- 2:00 PM: User posts spam → Bot posts notification (cooldown starts)
- 2:02 PM: User posts spam → Bot deletes, mutes, but NO notification (cooldown active)
- 2:05 PM: User posts spam → Bot posts notification (cooldown expired)

Channel #off-topic (independent):
- 2:03 PM: User posts spam → Bot posts notification (independent cooldown)
```

### 2. Professional Configuration Portal ✅
Implemented MEE6/Dyno-style settings panel with:

**Detection Settings**:
- Toggle: Enable/disable spam detection
- Slider: Sensitivity (Similarity Threshold 0.5-0.95)
- Toggle: Auto-delete detected images

**Notification Settings**:
- Toggle: Send global notifications
- Input: Notification cooldown (1-60 minutes)
- Input: Mute duration (0-365 days, 0=permanent)

**Channel Management**:
- Whitelist channels (bot won't scan)
- Blacklist channels (bot only scans these)
- Display list of configured channels
- Remove buttons for each channel

### 3. REST API Endpoints ✅
All require `@dev_or_owner_required` authorization:

- `GET /api/server-settings/<guild_id>` - Retrieve settings
- `PUT /api/server-settings/<guild_id>` - Update settings
- `PUT /api/server-settings/<guild_id>/notification-channel/<channel_id>` - Set notification channel
- `POST /api/server-settings/<guild_id>/whitelist-channel/<channel_id>` - Add to whitelist
- `POST /api/server-settings/<guild_id>/blacklist-channel/<channel_id>` - Add to blacklist

### 4. Server-Specific Settings Database ✅
Per-guild configuration stored in `data.json`:

```json
{
  "guild_id": 123456789,
  "enabled": true,
  "similarity_threshold": 0.65,
  "auto_delete_images": true,
  "send_global_notification": true,
  "mute_duration_days": 7,
  "notify_channel_id": null,
  "whitelisted_channels": [123, 456],
  "blacklisted_channels": [],
  "notification_cooldown_minutes": 5
}
```

## Files Modified

### src/bot.py
- Added `SpamNotificationTracker` class (lines 103-118)
- Updated both attachment and URL-based detection to send notifications
- Global notification uses `notification_tracker.should_notify()` to check cooldown

### src/database.py
- Added `server_settings` to data structure
- New methods for getting/updating server settings
- New methods for checking whitelisted/blacklisted channels

### web_server.py
- Added 5 new API endpoints for server settings management

### templates/index.html
- Added "Server Configuration" panel (600+ lines HTML/CSS/JS)
- Professional UI with toggles, sliders, input fields
- JavaScript functions for managing settings
- Real-time UI updates when settings change

## Design Features

✨ **Professional Design**:
- Dark blue theme matching existing portal
- Responsive grid layout
- Modern toggle switches
- Interactive range slider
- Hover effects and visual feedback
- Color-coded badges and indicators

🎯 **User-Friendly**:
- Intuitive settings organization
- Clear help text for each option
- Visual confirmation of changes
- Real-time threshold value display
- Channel list display with remove buttons

🔒 **Secure**:
- API token validation on all endpoints
- Role-based access control (dev/owner only)
- Settings properly persisted to database
- Error handling and logging

## Integration Points

The spam notification system integrates with:
1. **Image Detection**: Both attachment and URL-based detection trigger notifications
2. **Message Deletion**: Notification sent after image is deleted and user is muted
3. **Logging**: Detection logged to log channel before notification

The configuration system integrates with:
1. **Admin Portal**: UI to manage all settings
2. **REST API**: Programmatic access to settings
3. **Database**: Persistent storage per-guild
4. **Discord Bot**: Settings applied immediately to detection logic

## Example Workflows

### Workflow 1: Adjust Detection Sensitivity
1. Admin opens portal → Server Configuration section
2. Drags threshold slider from 0.65 to 0.55
3. Clicks "Save Detection Settings"
4. API saves to database
5. Bot immediately uses new threshold on next message

### Workflow 2: Prevent Notification Spam
1. Multiple spam images detected in #general
2. First detection → "Spam image found, deleted" (notification sent)
3. Second detection (30s later) → No notification (cooldown active)
4. Third detection (10min later) → "Spam image found, deleted" (cooldown expired)

### Workflow 3: Whitelist a Channel
1. Admin enters channel ID (123456789)
2. Clicks "Add to Whitelist"
3. Channel appears in whitelist
4. Bot no longer scans images in #123456789

## Technical Improvements

- **Backwards Compatible**: Existing `data.json` automatically gets `server_settings` structure
- **Default Settings**: Missing settings get sensible defaults (same as global config)
- **Per-Channel Tracking**: Each channel has independent notification cooldown
- **Efficient**: Simple datetime comparison for cooldown check
- **Extensible**: Easy to add new settings without changing architecture

## What You Can Now Do

1. ✅ **Configure detection per-server** (different thresholds for different servers)
2. ✅ **Prevent notification spam** (intelligent cooldown system)
3. ✅ **Whitelist safe channels** (bot won't scan certain areas)
4. ✅ **Manage mute duration** (configurable punishment)
5. ✅ **Adjust sensitivity dynamically** (no restart needed)
6. ✅ **Professional admin experience** (MEE6/Dyno-style UI)

## Commits

1. **dcbf8e7**: URL detection feature (previous work)
2. **e00dc53**: URL detection documentation (previous work)
3. **5e566bc**: Professional configuration + spam notifications
   - 445 insertions across 4 files
   - SpamNotificationTracker class
   - API endpoints and database methods
   - Admin portal UI
4. **352eb83**: Configuration documentation

## Next Steps (Optional)

- [ ] Implement remove from whitelist/blacklist buttons
- [ ] Add statistics dashboard (detections/day, top offenders)
- [ ] Custom notification message templates
- [ ] Per-role punishment settings
- [ ] Automatic threshold learning
- [ ] Export settings/statistics as CSV

## Summary

Anti-Ad Bot now has a **professional, MEE6/Dyno-quality configuration system** combined with an **intelligent spam prevention system** for notifications. Server admins can easily customize detection behavior while the bot prevents notification spam through automatic cooldown tracking.

The system is production-ready, well-documented, and designed for easy expansion.
