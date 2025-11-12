import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import sys
from pathlib import Path
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import config.config as config
from src.image_detector import ImageDetector
from src.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bot')

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize components
detector = ImageDetector(config.TRAINING_DATA_PATH, config.SIMILARITY_THRESHOLD)
db = Database()

def extract_image_urls(text: str) -> list:
    """
    Extract image URLs from message text.
    Supports Discord CDN links and common image hosting URLs.
    """
    if not text:
        return []
    
    # URL regex pattern
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    
    # Filter for image URLs
    image_urls = []
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')
    
    for url in urls:
        # Check if URL ends with image extension or contains image parameters
        if any(url.lower().endswith(ext) for ext in image_extensions):
            image_urls.append(url)
        # Check for Discord CDN URLs (they often have query parameters but are still images)
        elif 'cdn.discordapp.com' in url.lower() and ('/attachments/' in url.lower() or '/stickers/' in url.lower()):
            image_urls.append(url)
        # Check for other common image hosting sites
        elif any(host in url.lower() for host in ['imgur.com', 'giphy.com', 'tenor.com', 'media.discord']):
            image_urls.append(url)
    
    return image_urls

# Rate limiting
class RateLimiter:
    """Simple rate limiter."""
    def __init__(self, calls: int = 5, period: int = 60):
        self.calls = calls
        self.period = period
        self.clock = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if action is allowed."""
        now = datetime.now()
        if key not in self.clock:
            self.clock[key] = []
        
        # Remove old entries
        self.clock[key] = [t for t in self.clock[key] if (now - t).seconds < self.period]
        
        if len(self.clock[key]) < self.calls:
            self.clock[key].append(now)
            return True
        
        return False

rate_limiter = RateLimiter(calls=10, period=60)

# Track spam notifications per channel to avoid message spam
class SpamNotificationTracker:
    """Track spam notifications per channel to prevent message spam."""
    def __init__(self, cooldown_minutes: int = 5):
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.last_notification = {}
    
    def should_notify(self, channel_id: int) -> bool:
        """Check if we should send a notification for this channel."""
        now = datetime.now()
        
        if channel_id not in self.last_notification:
            self.last_notification[channel_id] = now
            return True
        
        if now - self.last_notification[channel_id] >= self.cooldown:
            self.last_notification[channel_id] = now
            return True
        
        return False

notification_tracker = SpamNotificationTracker(cooldown_minutes=5)

@tasks.loop(hours=1)
async def cleanup_cache():
    """Periodically clean up detection cache."""
    try:
        # Clear old cache entries
        detector.detection_cache.clear()
        logger.info("Cleared detection cache")
    except Exception as e:
        logger.error(f"Error cleaning up cache: {e}")


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f'Bot logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guild(s)')
    
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} command(s)')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')
    
    # Set bot status - now configurable
    try:
        # Map status type
        status_map = {
            'online': discord.Status.online,
            'idle': discord.Status.idle,
            'do_not_disturb': discord.Status.do_not_disturb,
            'invisible': discord.Status.invisible
        }
        status = status_map.get(config.BOT_STATUS, discord.Status.online)
        
        # Map activity type
        activity_type_map = {
            'playing': discord.ActivityType.playing,
            'streaming': discord.ActivityType.streaming,
            'listening': discord.ActivityType.listening,
            'watching': discord.ActivityType.watching
        }
        activity_type = activity_type_map.get(config.BOT_ACTIVITY_TYPE, discord.ActivityType.watching)
        
        # Create activity
        activity = discord.Activity(
            type=activity_type,
            name=config.BOT_ACTIVITY_TEXT
        )
        
        # Set presence
        await bot.change_presence(status=status, activity=activity)
        
        logger.info(f'Bot presence set: {config.BOT_STATUS} - {config.BOT_ACTIVITY_TYPE} {config.BOT_ACTIVITY_TEXT}')
    except Exception as e:
        logger.error(f'Error setting bot presence: {e}')
        # Fallback to default
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for spam images"
            )
        )
    
    # Start background tasks
    cleanup_cache.start()


@bot.event
async def on_message(message: discord.Message):
    """Handle incoming messages and check for spam images."""
    # Ignore bot's own messages
    if message.author.bot:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Check if message has attachments
    has_attachments = len(message.attachments) > 0
    
    # Check if message has image URLs
    image_urls = extract_image_urls(message.content)
    
    # Skip if no attachments and no URLs
    if not has_attachments and not image_urls:
        return
    
    # Check attachments
    if has_attachments:
        for attachment in message.attachments:
            # Only check image attachments
            if not attachment.content_type or not attachment.content_type.startswith('image/'):
                continue
            
            try:
                logger.info(f"Checking image attachment from {message.author.name}: {attachment.filename}")
                
                # Download image
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                        else:
                            logger.warning(f"Failed to download image: HTTP {resp.status}")
                            continue
                
                # Detect if image is similar to training data
                is_similar, confidence, matched_image = await detector.detect_similar_image(image_bytes)
                
                if is_similar:
                    logger.warning(
                        f"Detected spam image from {message.author.name} "
                        f"(confidence: {confidence:.2%}, matched: {matched_image})"
                    )
                    
                    # Delete the message
                    await message.delete()
                    
                    # Mute the user
                    await mute_user(
                        message.guild,
                        message.author,
                        f"Posting spam/advertisement image (matched: {matched_image}, confidence: {confidence:.2%})"
                    )
                    
                    # Log to log channel
                    await log_detection(message, matched_image, confidence)
                    
                    # Send global notification (only once per cooldown period)
                    if notification_tracker.should_notify(message.channel.id):
                        try:
                            await message.channel.send(
                                "Spam image found, deleted"
                            )
                        except Exception as e:
                            logger.error(f"Error sending notification: {e}")
                    
                    # Notify user via DM
                    await notify_user(message.author, matched_image, confidence)
                    
                    return  # Stop processing after first detection
                    
            except Exception as e:
                logger.error(f"Error processing attachment {attachment.filename}: {e}")
    
    # Check image URLs in message content
    if image_urls:
        for url in image_urls:
            try:
                logger.info(f"Checking image URL from {message.author.name}: {url[:80]}...")
                
                # Download image from URL
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                        else:
                            logger.warning(f"Failed to download URL image: HTTP {resp.status}")
                            continue
                
                # Detect if image is similar to training data
                is_similar, confidence, matched_image = await detector.detect_similar_image(image_bytes)
                
                if is_similar:
                    logger.warning(
                        f"Detected spam image URL from {message.author.name} "
                        f"(confidence: {confidence:.2%}, matched: {matched_image})"
                    )
                    
                    # Delete the message
                    await message.delete()
                    
                    # Mute the user
                    await mute_user(
                        message.guild,
                        message.author,
                        f"Posting spam/advertisement image via URL (matched: {matched_image}, confidence: {confidence:.2%})"
                    )
                    
                    # Log to log channel
                    await log_detection(message, matched_image, confidence)
                    
                    # Send global notification (only once per cooldown period)
                    if notification_tracker.should_notify(message.channel.id):
                        try:
                            await message.channel.send(
                                "Spam image found, deleted"
                            )
                        except Exception as e:
                            logger.error(f"Error sending notification: {e}")
                    
                    # Notify user via DM
                    await notify_user(message.author, matched_image, confidence)
                    
                    return  # Stop processing after first detection
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout downloading image URL from {message.author.name}")
                continue
            except Exception as e:
                logger.error(f"Error processing URL image from {message.author.name}: {e}")


async def mute_user(guild: discord.Guild, member: discord.Member, reason: str):
    """Mute a user by assigning the muted role."""
    try:
        # Check if user is already muted
        if db.is_muted(member.id):
            logger.info(f"User {member.name} is already muted")
            return
        
        # Check if member is a bot
        if member.bot:
            logger.warning(f"Attempted to mute bot {member.name}")
            return
        
        # Get muted role
        muted_role = guild.get_role(config.MUTED_ROLE_ID)
        
        if not muted_role:
            logger.error(f"Muted role not found (ID: {config.MUTED_ROLE_ID})")
            return
        
        # Check role hierarchy
        if muted_role.position >= guild.me.top_role.position:
            logger.error(f"Bot role is below muted role in hierarchy")
            return
        
        # Add muted role to user
        await member.add_roles(muted_role, reason=reason)
        
        # Save to database
        matched_image = reason.split('matched: ')[1].split(',')[0] if 'matched:' in reason else 'unknown'
        confidence = 0.0
        if 'confidence:' in reason:
            try:
                conf_str = reason.split('confidence: ')[1].rstrip('%').rstrip(')')
                confidence = float(conf_str) / 100
            except:
                confidence = 0.0
        
        db.add_muted_user(member.id, str(member), reason, matched_image, confidence)
        
        logger.info(f"Muted user {member.name} (ID: {member.id})")
        
    except discord.Forbidden:
        logger.error(f"Permission denied when muting user {member.name}")
    except Exception as e:
        logger.error(f"Error muting user {member.name}: {e}")


async def log_detection(message: discord.Message, matched_image: str, confidence: float):
    """Log detection to the log channel."""
    try:
        log_channel = bot.get_channel(config.LOG_CHANNEL_ID)
        
        if not log_channel:
            logger.warning(f"Log channel not found (ID: {config.LOG_CHANNEL_ID})")
            return
        
        embed = discord.Embed(
            title="🚨 Spam Image Detected",
            description=f"Detected and removed spam image from {message.author.mention}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="User", value=f"{message.author.name} ({message.author.id})", inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Confidence", value=f"{confidence:.2%}", inline=True)
        embed.add_field(name="Matched Image", value=matched_image, inline=False)
        
        embed.set_footer(text=f"User ID: {message.author.id}")
        
        if message.author.avatar:
            embed.set_thumbnail(url=message.author.avatar.url)
        
        await log_channel.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error logging detection: {e}")


async def notify_user(member: discord.Member, matched_image: str, confidence: float):
    """Send a DM to the muted user."""
    try:
        embed = discord.Embed(
            title="⚠️ You Have Been Muted",
            description="You have been automatically muted for posting spam/advertisement images.",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="Reason",
            value=f"Your image matched our spam detection system (confidence: {confidence:.2%})",
            inline=False
        )
        
        embed.add_field(
            name="Appeal Process",
            value=(
                "If you believe this was a mistake, you can submit an appeal using:\n"
                f"`/appeal <reason>`\n\n"
                "Your appeal will be reviewed by moderators."
            ),
            inline=False
        )
        
        await member.send(embed=embed)
        logger.info(f"Sent mute notification to {member.name}")
        
    except discord.Forbidden:
        logger.warning(f"Could not DM user {member.name} (DMs disabled)")
    except Exception as e:
        logger.error(f"Error notifying user {member.name}: {e}")


# Slash Commands

@bot.tree.command(name="appeal", description="Submit an appeal if you were wrongly muted")
@app_commands.describe(reason="Explain why you think you were wrongly muted")
async def appeal(interaction: discord.Interaction, reason: str):
    """Submit an appeal for being muted."""
    # Check if user is muted
    if not db.is_muted(interaction.user.id):
        await interaction.response.send_message(
            "❌ You are not currently muted.",
            ephemeral=True
        )
        return
    
    # Check if user already has a pending appeal
    muted_user = db.get_muted_user(interaction.user.id)
    if muted_user and muted_user['appeal_status'] == 'pending':
        await interaction.response.send_message(
            "⚠️ You already have a pending appeal. Please wait for moderators to review it.",
            ephemeral=True
        )
        return
    
    # Submit appeal
    appeal_index = db.add_appeal(interaction.user.id, str(interaction.user), reason)
    
    # Notify in appeal channel
    appeal_channel = bot.get_channel(config.APPEAL_CHANNEL_ID)
    if appeal_channel:
        embed = discord.Embed(
            title="📝 New Appeal",
            description=f"Appeal from {interaction.user.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="User", value=f"{interaction.user.name} ({interaction.user.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        if muted_user:
            embed.add_field(
                name="Original Detection",
                value=f"Matched: {muted_user['matched_image']}\nConfidence: {muted_user['confidence']:.2%}",
                inline=False
            )
        
        embed.set_footer(text=f"Appeal Index: {appeal_index}")
        
        await appeal_channel.send(embed=embed)
    
    await interaction.response.send_message(
        "✅ Your appeal has been submitted! Moderators will review it shortly.",
        ephemeral=True
    )


@bot.tree.command(name="approve_appeal", description="[ADMIN] Approve an appeal and unmute the user")
@app_commands.describe(appeal_index="The index of the appeal to approve")
@app_commands.default_permissions(administrator=True)
async def approve_appeal(interaction: discord.Interaction, appeal_index: int):
    """Approve an appeal and unmute the user."""
    appeals = db.get_pending_appeals()
    
    if appeal_index >= len(db.data['appeals']):
        await interaction.response.send_message(
            "❌ Invalid appeal index.",
            ephemeral=True
        )
        return
    
    appeal = db.data['appeals'][appeal_index]
    
    if appeal['status'] != 'pending':
        await interaction.response.send_message(
            f"❌ This appeal has already been {appeal['status']}.",
            ephemeral=True
        )
        return
    
    # Update appeal status
    db.update_appeal_status(appeal_index, 'approved')
    
    # Unmute user
    member = interaction.guild.get_member(appeal['user_id'])
    if member:
        muted_role = interaction.guild.get_role(config.MUTED_ROLE_ID)
        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role, reason=f"Appeal approved by {interaction.user.name}")
        
        # Remove from database
        db.unmute_user(appeal['user_id'])
        
        # Notify user
        try:
            embed = discord.Embed(
                title="✅ Appeal Approved",
                description="Your appeal has been approved and you have been unmuted!",
                color=discord.Color.green()
            )
            await member.send(embed=embed)
        except:
            pass
    
    await interaction.response.send_message(
        f"✅ Appeal approved! User <@{appeal['user_id']}> has been unmuted.",
        ephemeral=True
    )


@bot.tree.command(name="deny_appeal", description="[ADMIN] Deny an appeal")
@app_commands.describe(
    appeal_index="The index of the appeal to deny",
    reason="Reason for denial (optional)"
)
@app_commands.default_permissions(administrator=True)
async def deny_appeal(interaction: discord.Interaction, appeal_index: int, reason: Optional[str] = None):
    """Deny an appeal."""
    if appeal_index >= len(db.data['appeals']):
        await interaction.response.send_message(
            "❌ Invalid appeal index.",
            ephemeral=True
        )
        return
    
    appeal = db.data['appeals'][appeal_index]
    
    if appeal['status'] != 'pending':
        await interaction.response.send_message(
            f"❌ This appeal has already been {appeal['status']}.",
            ephemeral=True
        )
        return
    
    # Update appeal status
    db.update_appeal_status(appeal_index, 'denied')
    
    # Notify user
    member = interaction.guild.get_member(appeal['user_id'])
    if member:
        try:
            embed = discord.Embed(
                title="❌ Appeal Denied",
                description="Your appeal has been reviewed and denied.",
                color=discord.Color.red()
            )
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await member.send(embed=embed)
        except:
            pass
    
    await interaction.response.send_message(
        f"✅ Appeal denied for user <@{appeal['user_id']}>.",
        ephemeral=True
    )


@bot.tree.command(name="list_muted", description="[ADMIN] List all muted users")
@app_commands.default_permissions(administrator=True)
async def list_muted(interaction: discord.Interaction):
    """List all muted users."""
    muted_users = db.get_all_muted_users()
    
    if not muted_users:
        await interaction.response.send_message(
            "✅ No users are currently muted.",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="🔇 Muted Users",
        description=f"Total: {len(muted_users)} user(s)",
        color=discord.Color.orange()
    )
    
    for user in muted_users[:25]:  # Discord embed field limit
        embed.add_field(
            name=f"{user['username']} ({user['user_id']})",
            value=(
                f"**Matched:** {user['matched_image']}\n"
                f"**Confidence:** {user['confidence']:.2%}\n"
                f"**Appeal:** {user['appeal_status']}"
            ),
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="unmute", description="[ADMIN] Manually unmute a user")
@app_commands.describe(user="The user to unmute")
@app_commands.default_permissions(administrator=True)
async def unmute(interaction: discord.Interaction, user: discord.Member):
    """Manually unmute a user."""
    if not db.is_muted(user.id):
        await interaction.response.send_message(
            f"❌ {user.mention} is not muted.",
            ephemeral=True
        )
        return
    
    # Remove muted role
    muted_role = interaction.guild.get_role(config.MUTED_ROLE_ID)
    if muted_role and muted_role in user.roles:
        await user.remove_roles(muted_role, reason=f"Manually unmuted by {interaction.user.name}")
    
    # Remove from database
    db.unmute_user(user.id)
    
    # Notify user
    try:
        embed = discord.Embed(
            title="✅ You Have Been Unmuted",
            description="A moderator has unmuted you.",
            color=discord.Color.green()
        )
        await user.send(embed=embed)
    except:
        pass
    
    await interaction.response.send_message(
        f"✅ {user.mention} has been unmuted.",
        ephemeral=True
    )


@bot.tree.command(name="check_image", description="[ADMIN] Manually check an image URL")
@app_commands.describe(image_url="URL of the image to check")
@app_commands.default_permissions(administrator=True)
async def check_image(interaction: discord.Interaction, image_url: str):
    """Manually check an image URL."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Download image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send(
                        f"❌ Failed to download image: HTTP {resp.status}",
                        ephemeral=True
                    )
                    return
                
                image_bytes = await resp.read()
        
        # Check image
        is_similar, confidence, matched_image = await detector.detect_similar_image(image_bytes)
        
        embed = discord.Embed(
            title="🔍 Image Check Result",
            color=discord.Color.red() if is_similar else discord.Color.green()
        )
        
        embed.add_field(name="Similar to Training Data", value="Yes" if is_similar else "No", inline=True)
        embed.add_field(name="Confidence", value=f"{confidence:.2%}", inline=True)
        
        if is_similar:
            embed.add_field(name="Matched Image", value=matched_image, inline=False)
        
        embed.set_thumbnail(url=image_url)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.followup.send(
            f"❌ Error checking image: {str(e)}",
            ephemeral=True
        )


@bot.tree.command(name="stats", description="[ADMIN] View bot statistics")
@app_commands.default_permissions(administrator=True)
async def stats(interaction: discord.Interaction):
    """View bot statistics."""
    muted_users = db.get_all_muted_users()
    pending_appeals = db.get_pending_appeals()
    detector_stats = detector.get_stats()
    
    embed = discord.Embed(
        title="📊 Bot Statistics",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(name="Total Muted Users", value=str(len(muted_users)), inline=True)
    embed.add_field(name="Pending Appeals", value=str(len(pending_appeals)), inline=True)
    embed.add_field(name="Training Images", value=str(detector_stats['training_images']), inline=True)
    embed.add_field(name="Detection Threshold", value=f"{detector_stats['threshold']:.0%}", inline=True)
    embed.add_field(name="Avg Detection Time", value=f"{detector_stats['avg_detection_time']:.3f}s", inline=True)
    embed.add_field(name="Cache Size", value=str(detector_stats['cache_size']), inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# Run the bot
if __name__ == '__main__':
    try:
        bot.run(config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
