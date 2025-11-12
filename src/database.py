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
            'server_settings': {}
        }
        self.load()
    
    def load(self):
        """Load database from file."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"Database loaded from {self.db_file}")
            except Exception as e:
                logger.error(f"Error loading database: {e}")
        else:
            logger.info("No existing database found, starting fresh")
    
    def save(self):
        """Save database to file."""
        try:
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
    
    def get_server_settings(self, guild_id: int) -> Dict:
        """Get server settings for a guild. Returns defaults if not found."""
        guild_id_str = str(guild_id)
        if guild_id_str not in self.data['server_settings']:
            # Return default settings
            self.data['server_settings'][guild_id_str] = {
                'guild_id': guild_id,
                'enabled': True,
                'similarity_threshold': 0.65,
                'auto_delete_images': True,
                'send_global_notification': True,
                'mute_duration_days': 7,
                'notify_channel_id': None,
                'whitelisted_channels': [],
                'blacklisted_channels': [],
                'notification_cooldown_minutes': 5
            }
            self.save()
        return self.data['server_settings'][guild_id_str]
    
    def update_server_settings(self, guild_id: int, settings: Dict) -> Dict:
        """Update server settings for a guild."""
        guild_id_str = str(guild_id)
        current_settings = self.get_server_settings(guild_id)
        current_settings.update(settings)
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
