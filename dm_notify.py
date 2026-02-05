# dm_notify.py — Ultimate Alert System (DM ONLY - NO SERVER CHANNELS!)
import discord
from logger import logger
from config import OWNER_ID, DM_ALERTS, ALERT_COOLDOWN, MAX_ALERTS_PER_MINUTE
from db_manager import increment_stat
from filters import get_priority
import asyncio
import time
from collections import deque

# Rate limiting
alert_timestamps = deque(maxlen=MAX_ALERTS_PER_MINUTE)
last_alert_time = 0

async def alert(bot, title: str, details: str, priority: str = None, 
                embed_fields: list = None, quick_action_text: str = None):
    """
    Send alert to owner via DM ONLY
    
    Args:
        bot: Bot instance
        title: Alert title
        details: Alert details
        priority: Priority level (e.g., '🔴 CRITICAL')
        embed_fields: List of (name, value, inline) for additional info
        quick_action_text: Quick action options text (if applicable)
    """
    global last_alert_time
    
    if not DM_ALERTS:
        logger.debug('DM alerts disabled')
        return
    
    if OWNER_ID is None:
        logger.warning('OWNER_ID not set; cannot send DM alert')
        return
    
    # Rate limiting
    current_time = time.time()
    
    # Clean old timestamps
    cutoff = current_time - 60
    while alert_timestamps and alert_timestamps[0] < cutoff:
        alert_timestamps.popleft()
    
    # Check if rate limit exceeded
    if len(alert_timestamps) >= MAX_ALERTS_PER_MINUTE:
        logger.warning(f'Alert rate limit exceeded ({MAX_ALERTS_PER_MINUTE}/min)')
        return
    
    # Cooldown between alerts
    if current_time - last_alert_time < ALERT_COOLDOWN:
        await asyncio.sleep(ALERT_COOLDOWN - (current_time - last_alert_time))
    
    # Record timestamp
    alert_timestamps.append(current_time)
    last_alert_time = current_time
    
    # Increment stats
    increment_stat('total_alerts')
    
    # Send DM
    await _send_dm_alert(bot, title, details, priority or '⚪ UNKNOWN', embed_fields, quick_action_text)

async def _send_dm_alert(bot, title: str, details: str, priority: str, 
                         embed_fields: list = None, quick_action_text: str = None):
    """Send alert via DM to owner"""
    try:
        owner = await bot.fetch_user(OWNER_ID)
        if not owner:
            logger.warning('Owner user not found')
            return
        
        # Build embed
        from utils import get_color_for_priority
        color = get_color_for_priority(priority)
        
        embed = discord.Embed(
            title=f"{priority} {title}",
            description=details,
            color=color,
            timestamp=discord.utils.utcnow()
        )
        
        # Add fields if provided
        if embed_fields:
            for field in embed_fields:
                if len(field) == 3:
                    name, value, inline = field
                else:
                    name, value = field
                    inline = False
                embed.add_field(name=name, value=value, inline=inline)
        
        embed.set_footer(text="Q Bot Security Monitor")
        
        # Send embed
        await owner.send(embed=embed)
        
        # Send quick actions if available
        if quick_action_text:
            await owner.send(quick_action_text)
        
        logger.info(f'Alert sent to owner: {title}')
        
    except discord.Forbidden:
        logger.error('Cannot send DM to owner - DMs are closed')
    except Exception as e:
        logger.exception(f'Failed to send alert DM: {e}')

async def alert_simple(bot, message: str):
    """
    Send simple text alert (no embed)
    
    Args:
        bot: Bot instance
        message: Simple message text
    """
    if not DM_ALERTS or OWNER_ID is None:
        return
    
    try:
        owner = await bot.fetch_user(OWNER_ID)
        if owner:
            await owner.send(message)
            logger.info(f'Simple alert sent to owner')
    except Exception as e:
        logger.exception(f'Failed to send simple alert: {e}')

async def alert_critical(bot, title: str, details: str, quick_action_text: str = None):
    """
    Send critical priority alert
    
    Args:
        bot: Bot instance
        title: Alert title
        details: Details
        quick_action_text: Quick action options
    """
    await alert(bot, title, details, priority='🔴 CRITICAL', quick_action_text=quick_action_text)

async def alert_warning(bot, title: str, details: str, quick_action_text: str = None):
    """Send warning priority alert"""
    await alert(bot, title, details, priority='🟡 WARNING', quick_action_text=quick_action_text)

async def alert_info(bot, title: str, details: str):
    """Send info priority alert"""
    await alert(bot, title, details, priority='🟢 INFO')

def get_alert_stats() -> dict:
    """Get alert statistics"""
    from db_manager import load_db
    db = load_db()
    return db.get('stats', {})
