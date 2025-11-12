import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger('database')


class Database:
    """Simple JSON-based database for storing muted users and appeals."""
    
    def __init__(self, db_file: str = 'data.json'):
        self.db_file = db_file
        self.data = {
            'muted_users': {},
            'appeals': [],
            'server_settings': {},
            'detections': []  # list of detection event dicts
        }
        self.load()
    
    def load(self):
        """Load database from file."""
        if os.path.exists(self.db_file):
            # Check if it's a file (not a directory)
            if os.path.isdir(self.db_file):
                logger.warning(f"{self.db_file} is a directory, attempting to clean up and start fresh")
                try:
                    import shutil
                    shutil.rmtree(self.db_file, ignore_errors=True)
                    logger.info(f"Successfully removed directory {self.db_file}")
                except Exception as e:
                    logger.warning(f"Could not remove directory {self.db_file}: {e}, continuing with fresh data")
                # Continue with fresh data regardless of removal success
                return
            elif os.path.isfile(self.db_file):
                try:
                    with open(self.db_file, 'r', encoding='utf-8') as f:
                        self.data = json.load(f)
                    logger.info(f"Database loaded from {self.db_file}")
                    return
                except json.JSONDecodeError as e:
                    logger.warning(f"Database file corrupted: {e}, starting fresh")
                except Exception as e:
                    logger.error(f"Error loading database: {e}")
        
        logger.info("No existing database found, starting fresh")
    
    def save(self):
        """Save database to file."""
        try:
            # If data.json exists as a directory, try to clean it up first
            if os.path.exists(self.db_file) and os.path.isdir(self.db_file):
                logger.warning(f"Cleaning up directory at {self.db_file} before save")
                import shutil
                shutil.rmtree(self.db_file, ignore_errors=True)
            
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug("Database saved")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def add_muted_user(self, user_id: int, username: str, reason: str, 
                       matched_image: str, confidence: float):
        """Add a muted user to the database."""
        self.data['muted_users'][str(user_id)] = {
            'user_id': user_id,
            'username': username,
            'reason': reason,
            'matched_image': matched_image,
            'confidence': confidence,
            'muted_at': datetime.utcnow().isoformat(),
            'appeal_status': 'none'
        }
        self.save()
        logger.info(f"Added muted user: {username} (ID: {user_id})")
    
    def is_muted(self, user_id: int) -> bool:
        """Check if a user is muted."""
        return str(user_id) in self.data['muted_users']
    
    def get_muted_user(self, user_id: int) -> Optional[Dict]:
        """Get muted user information."""
        return self.data['muted_users'].get(str(user_id))
    
    def unmute_user(self, user_id: int) -> bool:
        """Remove a user from the muted list."""
        user_id_str = str(user_id)
        if user_id_str in self.data['muted_users']:
            del self.data['muted_users'][user_id_str]
            self.save()
            logger.info(f"Unmuted user ID: {user_id}")
            return True
        return False
    
    def add_appeal(self, user_id: int, username: str, reason: str):
        """Add an appeal to the database."""
        appeal = {
            'user_id': user_id,
            'username': username,
            'reason': reason,
            'submitted_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        self.data['appeals'].append(appeal)
        
        # Update muted user's appeal status
        if str(user_id) in self.data['muted_users']:
            self.data['muted_users'][str(user_id)]['appeal_status'] = 'pending'
        
        self.save()
        logger.info(f"Added appeal from user: {username} (ID: {user_id})")
        return len(self.data['appeals']) - 1  # Return appeal index
    
    def get_pending_appeals(self) -> List[Dict]:
        """Get all pending appeals."""
        return [a for a in self.data['appeals'] if a['status'] == 'pending']
    
    def update_appeal_status(self, appeal_index: int, status: str):
        """Update the status of an appeal."""
        if 0 <= appeal_index < len(self.data['appeals']):
            self.data['appeals'][appeal_index]['status'] = status
            user_id = self.data['appeals'][appeal_index]['user_id']
            
            if str(user_id) in self.data['muted_users']:
                self.data['muted_users'][str(user_id)]['appeal_status'] = status
            
            self.save()
            logger.info(f"Updated appeal {appeal_index} status to: {status}")
    
    def get_all_muted_users(self) -> List[Dict]:
        """Get all muted users."""
        return list(self.data['muted_users'].values())

    # ---------------- Detection events -----------------

    def add_detection_event(self,
                             guild_id: int,
                             channel_id: int,
                             user_id: int,
                             username: str,
                             matched_image: str,
                             confidence: float,
                             source: str,
                             message_id: Optional[int] = None,
                             action: str = 'muted') -> None:
        """Append a detection event to the database for portal analytics."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'guild_id': guild_id,
            'channel_id': channel_id,
            'user_id': user_id,
            'username': username,
            'matched_image': matched_image,
            'confidence': confidence,
            'source': source,  # attachment | url
            'message_id': message_id,
            'action': action
        }
        # Ensure list exists even if older data.json is missing the key
        self.data.setdefault('detections', [])
        self.data['detections'].append(event)
        # Keep only recent N events to prevent unbounded growth
        if len(self.data['detections']) > 5000:
            self.data['detections'] = self.data['detections'][-5000:]
        self.save()
        logger.debug(f"Recorded detection event for user_id={user_id} in guild_id={guild_id}")

    def get_recent_detections(self, limit: int = 50) -> List[Dict]:
        """Return most recent detection events (newest first)."""
        det = self.data.get('detections', [])
        # Sort by timestamp descending safely
        try:
            det_sorted = sorted(
                det,
                key=lambda e: e.get('timestamp') or '',
                reverse=True
            )
        except Exception:
            det_sorted = det[::-1]
        return det_sorted[:max(1, min(limit, 500))]

    def get_detection_stats(self, days: int = 7) -> Dict:
        """Return simple stats: total count, counts per day for last N days, last_detection_at."""
        from datetime import timedelta
        det = self.data.get('detections', [])
        now = datetime.utcnow()
        start = now - timedelta(days=days - 1)

        # Initialize day buckets
        by_day: Dict[str, int] = {}
        for i in range(days):
            day = (start + timedelta(days=i)).date().isoformat()
            by_day[day] = 0

        last_at = None
        for e in det:
            ts_str = e.get('timestamp')
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str)
            except Exception:
                continue
            day_key = ts.date().isoformat()
            if day_key in by_day:
                by_day[day_key] += 1
            if not last_at or ts > last_at:
                last_at = ts

        total = len(det)
        return {
            'total': total,
            'days': days,
            'by_day': by_day,
            'last_detection_at': last_at.isoformat() if last_at else None
        }
    
    def get_server_settings(self, guild_id: int) -> Dict:
        """Get server settings for a guild. Returns defaults if not found."""
        guild_id_str = str(guild_id)
        if guild_id_str not in self.data['server_settings']:
            # Return default settings
            self.data['server_settings'][guild_id_str] = {
                'guild_id': guild_id,
                'display_name': f'Guild {guild_id}',
                'enabled': True,
                'similarity_threshold': 0.65,
                'auto_delete_images': True,
                'send_global_notification': True,
                'mute_duration_days': 7,
                'notify_channel_id': None,
                'whitelisted_channels': [],
                'blacklisted_channels': [],
                'notification_cooldown_minutes': 5,
                'updated_at': datetime.utcnow().isoformat()
            }
            self.save()
        return self.data['server_settings'][guild_id_str]
    
    def update_server_settings(self, guild_id: int, settings: Dict) -> Dict:
        """Update server settings for a guild."""
        guild_id_str = str(guild_id)
        current_settings = self.get_server_settings(guild_id)
        current_settings.update(settings)
        current_settings['updated_at'] = datetime.utcnow().isoformat()
        current_settings.setdefault('display_name', f'Guild {guild_id}')
        self.data['server_settings'][guild_id_str] = current_settings
        self.save()
        logger.info(f"Updated server settings for guild {guild_id}")
        return current_settings
    
    def is_channel_whitelisted(self, guild_id: int, channel_id: int) -> bool:
        """Check if a channel is whitelisted (bot won't scan there)."""
        settings = self.get_server_settings(guild_id)
        return channel_id in settings['whitelisted_channels']
    
    def is_channel_blacklisted(self, guild_id: int, channel_id: int) -> bool:
        """Check if a channel is blacklisted (bot will only scan there if set)."""
        settings = self.get_server_settings(guild_id)
        return channel_id in settings['blacklisted_channels']
