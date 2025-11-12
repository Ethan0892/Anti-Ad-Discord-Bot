# Anti-Ad Bot - Feature Roadmap

## Overview
Anti-Ad Bot is evolving from a specialized spam-image detection tool into a **comprehensive Discord moderation platform** that can compete with leading bots like Maki, Dyno, and Sapphire.

---

## ✅ Currently Implemented

### Core Features
- ✅ **Advanced Spam Image Detection** (5-algorithm hybrid system)
  - SIFT, ORB, Histogram, SSIM, Template Matching
  - 0.65 similarity threshold (highly tuned)
  - Confidence scoring & logging
  
- ✅ **Appeal System**
  - User-initiated appeals with reasons
  - Admin approval/denial workflow
  - Mute tracking & history
  
- ✅ **Admin Portal (Web UI)**
  - Training image management
  - GitHub sync for training data
  - Configuration panel
  - User management (Owner/Dev roles)
  - Role-based access control
  
- ✅ **Configurable Punishments**
  - Mute (automatic, tracked)
  - Timeout (timed enforcement)
  - Kick (removal)
  - Ban (permanent block)
  - Progressive enforcement (first/second offense different actions)

---

## 🚀 Planned Features (High Priority)

### Moderation Suite
- [ ] **User Warnings System**
  - `/warn @user [reason]` - Add strike against user
  - `/warnings @user` - Check user's warning count
  - Auto-action at N warnings (e.g., mute at 3, ban at 5)
  - Warning expiration (30-day rolling window)
  - Reason tracking & history

- [ ] **Message Moderation**
  - Spam detection (rapid message flooding)
  - Profanity filtering (configurable word lists)
  - Caps lock spam (EXCESSIVE MESSAGES IN ALL CAPS)
  - Mention spam (@everyone/@here spam detection)
  - URL/Link filtering (whitelist/blacklist domains)

- [ ] **User Management**
  - `/mute @user [duration] [reason]` - Manual mute with tracking
  - `/unmute @user [reason]` - Manual unmute with logging
  - `/kick @user [reason]` - Remove user from server
  - `/ban @user [reason]` - Permanent ban with logging
  - `/tempban @user [duration] [reason]` - Temporary ban
  - Ban appeal system for non-image violations

- [ ] **Moderation Logging**
  - Unified modlog channel with embeds
  - Track: mutes, unmutes, kicks, bans, warns, appeals
  - Before/after user context (join date, roles, history)
  - Moderator attribution & timestamp
  - Searchable modlog dashboard

- [ ] **Auto-Moderation Rules**
  - Configurable triggers (word patterns, rate limits, etc.)
  - Progressive enforcement (warn → timeout → mute → kick → ban)
  - Bypass roles (trusted users don't trigger rules)
  - Log all actions with reason

### Member Management
- [ ] **Leveling System** (Basic)
  - Track XP per message (configurable multiplier)
  - Leaderboard (`/leaderboard [page]`)
  - Level-up notifications (optional channel)
  - Custom level requirements
  - Role rewards at certain levels

- [ ] **Member Profiles**
  - `/profile @user` - Show user stats
  - Join date, message count, level, warnings, mutes
  - Last active timestamp
  - Server achievements/badges

- [ ] **Welcome System**
  - Customizable welcome message
  - Auto-assign member role
  - Welcome DM to new users
  - Optional verification requirement before access

### Advanced Features
- [ ] **Ticket System**
  - `/ticket [topic]` - Create support ticket
  - Auto-create private channels
  - Assign to staff members
  - Close with summary transcript
  - Category-based routing

- [ ] **Reaction Roles**
  - Setup message with emoji reactions
  - Users click emoji → auto-assign role
  - Dashboard to manage reaction messages
  - Configurable role groups

- [ ] **Autorole Manager**
  - Auto-assign roles on join
  - Role persistence (restore on rejoin)
  - Configurable per-role

### Statistics & Analytics
- [ ] **Server Statistics**
  - Member growth chart
  - Message activity heatmap
  - Most active channels
  - Peak hours analysis
  - Moderation action trends

- [ ] **User Analytics**
  - Message history per user
  - Activity patterns
  - Interaction graphs
  - Engagement metrics

---

## 📋 Medium Priority Features

- [ ] **Auto-Moderator Commands**
  - `/automod enable [rule]` - Enable automation
  - `/automod disable [rule]` - Disable automation
  - `/automod list` - Show active rules

- [ ] **Server Settings Dashboard**
  - `/settings` - Interactive config menu
  - Prefix customization
  - Language options
  - Timezone for timestamps
  - Modlog channel selection

- [ ] **Badword/Slur Detection**
  - Configurable word list
  - Auto-delete + warn
  - Partial word matching
  - Regex support

- [ ] **Role Management Helpers**
  - Bulk role assignment
  - Role templates
  - Role hierarchy display
  - Permission checker

---

## 🔮 Future/Lower Priority

- [ ] **Backup & Restore**
  - Server settings backup
  - Role backup
  - Channel structure snapshot

- [ ] **Custom Commands**
  - User-created commands with responses
  - Placeholder variables (username, server, etc.)
  - Cooldown settings

- [ ] **Music Bot Integration** (Separate plugin)
  - Queue management
  - Playlist support
  - Now playing display

- [ ] **Streaming Integration**
  - Twitch/YouTube stream announcements
  - Role assignment for streamers
  - Stream schedule

- [ ] **AFK Management**
  - Auto-assign AFK role
  - Auto-move to AFK voice channel
  - Remove on activity

---

## 🎯 Competitive Analysis vs. Popular Bots

| Feature | Anti-Ad | Maki | Dyno | Sapphire | YAGPDB |
|---------|---------|------|------|----------|--------|
| **Spam Image Detection** | ⭐⭐⭐⭐⭐ | ❌ | ❌ | ❌ | ❌ |
| **Moderation Suite** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Leveling** | 🚧 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Appeal System** | ⭐⭐⭐⭐ | ❌ | ⭐⭐ | ⭐⭐⭐ | ❌ |
| **Admin Portal** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| **Free** | ✅ | ❌ | Limited | ✅ | ✅ |
| **Open Source** | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Self-Hosted** | ✅ | ❌ | ❌ | Limited | ✅ |

---

## Implementation Priority

### Phase 1 (Next)
1. Warnings system + auto-actions
2. Basic message moderation (spam detection, caps)
3. Manual moderation commands (mute/unmute/kick/ban)
4. Improved modlog channel

### Phase 2
1. Leveling system (basic)
2. Moderation logging improvements
3. User profiles/stats
4. Leaderboard

### Phase 3
1. Ticket system
2. Reaction roles
3. Advanced analytics
4. Auto-moderation rules engine

---

## Why This Matters

**Current Situation:**
- Users choosing between MEE6 (paid), Maki (limited free tier), or complex bots like Sapphire
- No single free bot dominates for smaller communities

**Anti-Ad Opportunity:**
- **Specialized advantage**: Only bot with AI spam image detection
- **Free & Self-Hosted**: Full control, no subscription
- **Open Source**: Community contributions possible
- **Comprehensive**: Combines image detection + full moderation

**Target**: Become the **go-to free moderation bot for communities that value automated anti-spam detection**.

---

## Development Notes

- All features use slash commands (`/`) for modern Discord UX
- Admin portal dashboard updated with each feature
- Comprehensive logging for transparency
- Role-based access control maintained
- Database-backed (JSON for now, SQL ready)

---

## Community Feedback Welcome!

Have ideas? Want a specific feature?
- Open a GitHub issue
- Submit a PR
- Discussion in Discord

Let's build the best moderation solution! 🚀
