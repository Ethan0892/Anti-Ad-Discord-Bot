"""
Setup wizard for Discord Anti-Ad Bot
Helps configure the bot with interactive prompts
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key
import discord

def get_env_file():
    """Get or create .env file."""
    # Look for .env in config/ folder
    env_file = Path(__file__).parent.parent / 'config' / '.env'
    if not env_file.exists():
        example_file = Path(__file__).parent.parent / 'config' / '.env.example'
        if example_file.exists():
            with open(example_file, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ Created .env from .env.example")
        else:
            print("❌ .env.example not found!")
            sys.exit(1)
    return env_file

def setup_token(env_file):
    """Setup Discord bot token."""
    print("\n" + "="*60)
    print("🔐 Discord Bot Token Setup")
    print("="*60)
    print("\n1. Go to https://discord.com/developers/applications")
    print("2. Create New Application or select existing one")
    print("3. Go to 'Bot' section")
    print("4. Click 'Reset Token' and copy it")
    
    while True:
        token = input("\nEnter your bot token: ").strip()
        if token and len(token) > 50:
            set_key(env_file, "DISCORD_TOKEN", token)
            print("✅ Bot token saved!")
            return True
        else:
            print("❌ Invalid token. Try again.")

def setup_guild(env_file):
    """Setup guild/server ID."""
    print("\n" + "="*60)
    print("🖥️  Server Setup")
    print("="*60)
    print("\n1. Right-click your Discord server icon")
    print("2. Enable 'Developer Mode' in User Settings > Advanced > Developer Mode")
    print("3. Right-click server icon again")
    print("4. Click 'Copy Server ID'")
    
    while True:
        guild_id = input("\nEnter your server ID: ").strip()
        if guild_id.isdigit():
            set_key(env_file, "GUILD_ID", guild_id)
            print("✅ Server ID saved!")
            return True
        else:
            print("❌ Invalid ID. Must be numeric.")

def setup_muted_role(env_file):
    """Setup muted role."""
    print("\n" + "="*60)
    print("🔇 Muted Role Setup")
    print("="*60)
    print("\n1. Create a new role named 'Muted' (or preferred name)")
    print("2. Configure permissions:")
    print("   - Deny 'Send Messages' in all text channels")
    print("   - Deny 'Add Reactions'")
    print("   - Deny 'Speak' in all voice channels")
    print("3. Right-click the role")
    print("4. Click 'Copy Role ID'")
    
    while True:
        role_id = input("\nEnter the Muted role ID: ").strip()
        if role_id.isdigit():
            set_key(env_file, "MUTED_ROLE_ID", role_id)
            print("✅ Muted role ID saved!")
            return True
        else:
            print("❌ Invalid ID. Must be numeric.")

def setup_channels(env_file):
    """Setup required channels."""
    print("\n" + "="*60)
    print("📢 Channel Setup")
    print("="*60)
    print("\nYou need to create two channels:")
    print("1. #appeals - for users to submit appeals")
    print("2. #mod-logs - for detection logs")
    
    print("\nTo get channel ID:")
    print("- Right-click the channel")
    print("- Click 'Copy Channel ID'")
    
    # Appeals channel
    while True:
        appeal_channel = input("\nEnter appeals channel ID: ").strip()
        if appeal_channel.isdigit():
            set_key(env_file, "APPEAL_CHANNEL_ID", appeal_channel)
            print("✅ Appeals channel ID saved!")
            break
        else:
            print("❌ Invalid ID. Must be numeric.")
    
    # Log channel
    while True:
        log_channel = input("Enter mod-logs channel ID: ").strip()
        if log_channel.isdigit():
            set_key(env_file, "LOG_CHANNEL_ID", log_channel)
            print("✅ Log channel ID saved!")
            break
        else:
            print("❌ Invalid ID. Must be numeric.")

def setup_threshold(env_file):
    """Setup detection threshold."""
    print("\n" + "="*60)
    print("🎯 Detection Threshold Setup")
    print("="*60)
    print("\nThreshold determines sensitivity:")
    print("- 0.75-0.80: More aggressive (catches more spam)")
    print("- 0.85 (default): Balanced")
    print("- 0.90-0.95: Conservative (fewer false positives)")
    
    while True:
        threshold = input("\nEnter threshold (0.0-1.0) [default 0.85]: ").strip()
        if not threshold:
            set_key(env_file, "SIMILARITY_THRESHOLD", "0.85")
            print("✅ Threshold set to 0.85 (default)")
            break
        try:
            val = float(threshold)
            if 0.0 <= val <= 1.0:
                set_key(env_file, "SIMILARITY_THRESHOLD", threshold)
                print(f"✅ Threshold set to {val}")
                break
            else:
                print("❌ Value must be between 0.0 and 1.0")
        except ValueError:
            print("❌ Invalid value. Enter a decimal number.")

def setup_training_data():
    """Check training data."""
    print("\n" + "="*60)
    print("📸 Training Data Setup")
    print("="*60)
    
    training_dir = Path("Training-Data")
    if not training_dir.exists():
        training_dir.mkdir(exist_ok=True)
        print("✅ Created Training-Data directory")
        print("\n⚠️  Add your spam/advertisement images to Training-Data/")
        print("Supported formats: PNG, JPG, JPEG, GIF, WEBP, BMP")
        return False
    
    images = list(training_dir.glob("*.*"))
    image_count = sum(1 for f in images if f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'})
    
    if image_count == 0:
        print("\n⚠️  No images found in Training-Data/")
        print("Add spam/advertisement images for the bot to learn from.")
        return False
    else:
        print(f"\n✅ Found {image_count} training image(s)")
        for img in training_dir.glob("*.*"):
            if img.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}:
                print(f"  - {img.name}")
        return True

def verify_permissions():
    """Verify bot has required permissions."""
    print("\n" + "="*60)
    print("🔑 Bot Permissions")
    print("="*60)
    print("\nEnsure your bot has these permissions:")
    print("✓ Manage Roles")
    print("✓ Manage Messages")
    print("✓ Send Messages")
    print("✓ Embed Links")
    print("✓ Read Message History")
    print("\nGenerate invite URL:")
    print("https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=268435456&scope=bot%20applications.commands")

def main():
    """Run setup wizard."""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║      Discord Anti-Ad Bot - Setup Wizard                       ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required!")
            sys.exit(1)
        
        # Get or create .env file
        env_file = get_env_file()
        load_dotenv(env_file)
        
        # Run setup steps
        setup_token(env_file)
        setup_guild(env_file)
        setup_muted_role(env_file)
        setup_channels(env_file)
        setup_threshold(env_file)
        setup_training_data()
        verify_permissions()
        
        print("\n" + "="*60)
        print("✅ Setup Complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Add training images to Training-Data/ folder")
        print("3. Run the bot: python bot.py")
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
