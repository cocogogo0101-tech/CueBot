# mask.py — Auto-Reply Mask System
import discord
from db_manager import load_db, save_db
from logger import logger
from config import GUILD_ID

def set_mask_channel_by_id(channel_id: int):
    """Set mask channel (used by slash command)"""
    db = load_db()
    db['mask']['channel_id'] = str(channel_id)
    save_db(db)
    logger.info(f"Mask channel set to {channel_id}")

async def on_message_mask(bot, message: discord.Message):
    """Handle mask auto-reply"""
    # Only in guild channels
    if message.guild is None:
        return
    
    # Check guild
    if GUILD_ID and message.guild.id != GUILD_ID:
        return
    
    # Ignore bots
    if message.author.bot:
        return
    
    # Get mask settings
    db = load_db()
    mask_channel_id = db.get('mask', {}).get('channel_id')
    
    if mask_channel_id is None:
        return
    
    # Check if message is in mask channel
    if str(message.channel.id) != str(mask_channel_id):
        return
    
    # Get reply text
    reply_text = db.get('mask', {}).get('reply_text') or '━━━━━━━━━━━━'
    
    # Send reply
    try:
        await message.channel.send(reply_text)
        logger.info(f'Mask replied in channel {message.channel.id} for message {message.id}')
    except Exception as e:
        logger.exception(f'Mask reply failed: {e}')
