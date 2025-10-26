import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env - check multiple locations for Docker and local compatibility
config_dir = Path(__file__).parent
root_dir = config_dir.parent

# Try loading from config directory first, then root
env_paths = [
    config_dir / '.env',
    root_dir / '.env',
    '.env'
]

for env_file in env_paths:
    if env_file.exists():
        load_dotenv(env_file)
        break
else:
    # If no .env found, try loading from environment variables (Docker)
    load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))
MUTED_ROLE_ID = int(os.getenv('MUTED_ROLE_ID', 0))
APPEAL_CHANNEL_ID = int(os.getenv('APPEAL_CHANNEL_ID', 0))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', 0))

# Image Detection Settings
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.75))
TRAINING_DATA_PATH = str(Path(__file__).parent.parent / 'Training-Data')

# Punishment Settings (Configurable)
PUNISHMENT_TYPE = os.getenv('PUNISHMENT_TYPE', 'mute').lower()  # 'mute', 'timeout', 'kick', 'ban'
MUTE_DURATION_DAYS = int(os.getenv('MUTE_DURATION_DAYS', 7))  # Days for permanent mute (0 = permanent)
TIMEOUT_DURATION_MINUTES = int(os.getenv('TIMEOUT_DURATION_MINUTES', 60))  # Minutes to timeout user
FIRST_OFFENSE_ACTION = os.getenv('FIRST_OFFENSE_ACTION', 'mute')  # Action for first offense
SECOND_OFFENSE_ACTION = os.getenv('SECOND_OFFENSE_ACTION', 'timeout')  # Action for second offense
THIRD_OFFENSE_ACTION = os.getenv('THIRD_OFFENSE_ACTION', 'kick')  # Action for third offense
AUTO_DELETE_IMAGE = os.getenv('AUTO_DELETE_IMAGE', 'true').lower() == 'true'  # Auto-delete detected images
AUTO_DELETE_DELAY = int(os.getenv('AUTO_DELETE_DELAY', 0))  # Seconds to wait before deleting (0 = instant)

# Logging
LOG_DETECTIONS = os.getenv('LOG_DETECTIONS', 'true').lower() == 'true'
LOG_APPEALS = os.getenv('LOG_APPEALS', 'true').lower() == 'true'

# Bot Presence Configuration
# Status type: online, idle, do_not_disturb, invisible
BOT_STATUS = os.getenv('BOT_STATUS', 'online').lower()  

# Activity type: playing, streaming, listening, watching
# Examples: "watching for spam" or "playing with filters"
BOT_ACTIVITY_TYPE = os.getenv('BOT_ACTIVITY_TYPE', 'watching').lower()  
BOT_ACTIVITY_TEXT = os.getenv('BOT_ACTIVITY_TEXT', 'for spam images')

# Validate required settings
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is required in .env file")
