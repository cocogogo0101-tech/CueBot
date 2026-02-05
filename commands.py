# commands.py — ULTIMATE DM Command System (Owner Only)
import discord
from db_manager import load_db, save_db, add_to_audit_log
from logger import logger
from dm_notify import alert_simple, get_alert_stats
from config import OWNER_ID, GUILD_ID, PREFIX
from filters import *
from whitelist import *
from quick_actions import handle_quick_action_response, get_pending_actions_count, pending_actions
from utils import parse_user_id, format_user, format_timestamp
from permissions import format_role_info, analyze_permissions
import datetime

async def handle_dm(bot, message: discord.Message):
    """Handle DM commands from owner"""
    # Enforce DM + owner only
    if message.guild is not None:
        return
    
    if OWNER_ID is None or message.author.id != OWNER_ID:
        return
    
    content = message.content.strip()
    if not content:
        return
    
    # Check if it's a quick action response (just a number)
    if content.isdigit() and get_pending_actions_count() > 0:
        await _handle_quick_action_number(bot, message, int(content))
        return
    
    # Check if it's a quick action ID response (e.g., "ABC123 2")
    parts = content.split()
    if len(parts) == 2 and parts[0].isalnum() and len(parts[0]) == 6 and parts[1].isdigit():
        action_id = parts[0].upper()
        choice = int(parts[1])
        result = await handle_quick_action_response(bot, message, action_id, choice)
        await message.author.send(result)
        return
    
    # Regular commands
    if not content.startswith(PREFIX):
        return
    
    # Remove prefix and split
    content = content[len(PREFIX):]
    parts = content.split()
    if not parts:
        return
    
    keyword = parts[0].lower()
    
    # ============= HELP COMMAND =============
    if keyword in ('help', 'مساعدة', 'مساعده'):
        await _cmd_help(message)
        return
    
    # ============= WATCH COMMANDS =============
    if keyword in ('watch', 'راقب'):
        await _cmd_watch(message, parts)
        return
    
    if keyword in ('unwatch', 'الغاء', 'إلغاء'):
        await _cmd_unwatch(message, parts)
        return
    
    if keyword in ('list', 'قائمة', 'قايمة'):
        await _cmd_list_watched(message)
        return
    
    # ============= WHITELIST COMMANDS =============
    if keyword in ('whitelist', 'موثوق'):
        await _cmd_whitelist(message, parts)
        return
    
    if keyword in ('unwhitelist', 'حذف_موثوق'):
        await _cmd_unwhitelist(message, parts)
        return
    
    if keyword in ('listwhite', 'قايمة_موثوق'):
        await _cmd_list_whitelist(message)
        return
    
    # ============= FILTER COMMANDS =============
    if keyword in ('filter', 'فلتر'):
        await _cmd_filter(message, parts)
        return
    
    if keyword in ('filters', 'الفلاتر'):
        await _cmd_filters_status(message)
        return
    
    # ============= INFO COMMANDS =============
    if keyword in ('info', 'معلومات'):
        await _cmd_info(message, parts, bot)
        return
    
    if keyword in ('logs', 'سجل'):
        await _cmd_logs(message, parts)
        return
    
    if keyword in ('stats', 'احصائيات'):
        await _cmd_stats(message)
        return
    
    # ============= MODERATION COMMANDS =============
    if keyword in ('strip', 'سحب'):
        await _cmd_strip(message, parts, bot)
        return
    
    if keyword in ('ban', 'حظر'):
        await _cmd_ban(message, parts, bot)
        return
    
    if keyword in ('kick', 'طرد'):
        await _cmd_kick(message, parts, bot)
        return
    
    if keyword in ('timeout', 'كتم'):
        await _cmd_timeout(message, parts, bot)
        return
    
    # ============= GUILD INFO COMMANDS =============
    if keyword in ('channels', 'قنوات'):
        await _cmd_channels(message, bot)
        return
    
    if keyword in ('roles', 'رتب', 'الرتب'):
        await _cmd_roles(message, bot)
        return
    
    if keyword in ('members', 'اعضاء'):
        await _cmd_members(message, bot)
        return
    
    # ============= SETTINGS COMMANDS =============
    if keyword in ('settings', 'اعدادات'):
        await _cmd_settings(message)
        return
    
    # ============= MASK COMMANDS =============
    if keyword == 'mask':
        await _cmd_mask(message, parts, content)
        return
    
    # Unknown command
    await message.author.send(f'❌ Unknown command: `{keyword}`\nSend `.help` for list.')

# =====================================================
# COMMAND IMPLEMENTATIONS
# =====================================================

async def _handle_quick_action_number(bot, message: discord.Message, choice: int):
    """Handle quick action when user sends just a number"""
    # Get most recent action
    if not pending_actions:
        await message.author.send('❌ No pending quick actions')
        return
    
    # Get the most recent action (last added)
    action_id = list(pending_actions.keys())[-1]
    
    result = await handle_quick_action_response(bot, message, action_id, choice)
    await message.author.send(result)

async def _cmd_help(message: discord.Message):
    """Help command"""
    help_text = f"""
**Q Bot - DM Commands** 🛡️
*All commands start with `{PREFIX}`*

**📋 Monitoring:**
`{PREFIX}watch <user_id>` / `{PREFIX}راقب <id>` - Watch a user
`{PREFIX}unwatch <user_id>` / `{PREFIX}الغاء <id>` - Stop watching
`{PREFIX}list` / `{PREFIX}قائمة` - List watched users
`{PREFIX}info <user_id>` / `{PREFIX}معلومات` - Get user info
`{PREFIX}logs <user_id>` - View user activity logs

**✅ Whitelist:**
`{PREFIX}whitelist <user_id>` - Add to whitelist
`{PREFIX}unwhitelist <user_id>` - Remove from whitelist
`{PREFIX}listwhite` - Show whitelist

**🔧 Filters:**
`{PREFIX}filter <name> on/off` - Toggle filter
`{PREFIX}filter all on/off` - Toggle all filters
`{PREFIX}filter reset` - Reset to defaults
`{PREFIX}filters` - Show all filters

**⚔️ Moderation:**
`{PREFIX}strip <user_id>` / `{PREFIX}سحب` - Remove all roles
`{PREFIX}ban <user_id>` / `{PREFIX}حظر` - Ban user
`{PREFIX}kick <user_id>` / `{PREFIX}طرد` - Kick user
`{PREFIX}timeout <user_id> [minutes]` - Timeout user

**📊 Server Info:**
`{PREFIX}channels` / `{PREFIX}قنوات` - List channels
`{PREFIX}roles` / `{PREFIX}رتب` - List roles
`{PREFIX}members` - List members (summary)
`{PREFIX}stats` / `{PREFIX}احصائيات` - Bot statistics

**⚙️ Settings:**
`{PREFIX}settings` - View current settings
`{PREFIX}mask set_channel <id>` - Set mask channel
`{PREFIX}mask set_reply <text>` - Set mask reply
`{PREFIX}mask clear` - Clear mask

**⚡ Quick Actions:**
When you get an alert with quick actions, reply with:
• Just the number (e.g., `1`) for the most recent action
• Or `ACTION_ID NUMBER` (e.g., `ABC123 1`)

**💡 Tip:** Watched users get detailed monitoring (messages, etc.)
    """
    await message.author.send(help_text)

async def _cmd_watch(message: discord.Message, parts: list):
    """Watch a user"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.watch <user_id>`')
        return
    
    user_id = parse_user_id(parts[1])
    if user_id is None:
        await message.author.send('❌ Invalid user ID')
        return
    
    user_id_str = str(user_id)
    db = load_db()
    
    if user_id_str in db.get('watched_users', []):
        await message.author.send(f'⚠️ Already watching user `{user_id}`')
        return
    
    db.setdefault('watched_users', []).append(user_id_str)
    save_db(db)
    
    add_to_audit_log('watch_added', {'user_id': user_id})
    
    await message.author.send(f'✅ Now watching user `{user_id}`')
    logger.info(f'Owner added watch for user {user_id}')

async def _cmd_unwatch(message: discord.Message, parts: list):
    """Stop watching a user"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.unwatch <user_id>`')
        return
    
    user_id = parse_user_id(parts[1])
    if user_id is None:
        await message.author.send('❌ Invalid user ID')
        return
    
    user_id_str = str(user_id)
    db = load_db()
    
    if user_id_str not in db.get('watched_users', []):
        await message.author.send(f'⚠️ User `{user_id}` not in watch list')
        return
    
    db['watched_users'].remove(user_id_str)
    save_db(db)
    
    add_to_audit_log('watch_removed', {'user_id': user_id})
    
    await message.author.send(f'✅ Stopped watching user `{user_id}`')
    logger.info(f'Owner removed watch for user {user_id}')

async def _cmd_list_watched(message: discord.Message):
    """List watched users"""
    db = load_db()
    watched = db.get('watched_users', [])
    
    if not watched:
        await message.author.send('📋 **Watched Users:** None')
        return
    
    lines = ['📋 **Watched Users:**\n']
    for i, uid in enumerate(watched, 1):
        lines.append(f'{i}. `{uid}`')
    
    await message.author.send('\n'.join(lines))

async def _cmd_whitelist(message: discord.Message, parts: list):
    """Add user to whitelist"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.whitelist <user_id>`')
        return
    
    user_id = parse_user_id(parts[1])
    if user_id is None:
        await message.author.send('❌ Invalid user ID')
        return
    
    success, msg = add_to_whitelist(user_id)
    await message.author.send(msg)

async def _cmd_unwhitelist(message: discord.Message, parts: list):
    """Remove user from whitelist"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.unwhitelist <user_id>`')
        return
    
    user_id = parse_user_id(parts[1])
    if user_id is None:
        await message.author.send('❌ Invalid user ID')
        return
    
    success, msg = remove_from_whitelist(user_id)
    await message.author.send(msg)

async def _cmd_list_whitelist(message: discord.Message):
    """List whitelisted users"""
    msg = get_whitelist_display()
    await message.author.send(msg)

async def _cmd_filter(message: discord.Message, parts: list):
    """Manage filters"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.filter <name> on/off` or `.filter all on/off` or `.filter reset`')
        return
    
    sub = parts[1].lower()
    
    # Reset filters
    if sub == 'reset':
        msg = reset_filters()
        await message.author.send(msg)
        return
    
    # Toggle all
    if sub == 'all':
        if len(parts) < 3:
            await message.author.send('❌ Usage: `.filter all on/off`')
            return
        
        action = parts[2].lower()
        if action in ('on', 'تشغيل'):
            msg = enable_all_filters()
        elif action in ('off', 'ايقاف', 'إيقاف'):
            msg = disable_all_filters()
        else:
            await message.author.send('❌ Use `on` or `off`')
            return
        
        await message.author.send(msg)
        return
    
    # Toggle specific filter
    if len(parts) < 3:
        await message.author.send('❌ Usage: `.filter <name> on/off`')
        return
    
    filter_name = sub
    action = parts[2].lower()
    
    if action in ('on', 'تشغيل'):
        success, msg = set_filter(filter_name, True)
    elif action in ('off', 'ايقاف', 'إيقاف'):
        success, msg = set_filter(filter_name, False)
    else:
        await message.author.send('❌ Use `on` or `off`')
        return
    
    await message.author.send(msg)

async def _cmd_filters_status(message: discord.Message):
    """Show all filters status"""
    msg = get_filters_status()
    await message.author.send(msg)

async def _cmd_info(message: discord.Message, parts: list, bot):
    """Get user info"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.info <user_id>`')
        return
    
    user_id = parse_user_id(parts[1])
    if user_id is None:
        await message.author.send('❌ Invalid user ID')
        return
    
    if GUILD_ID is None:
        await message.author.send('❌ GUILD_ID not configured')
        return
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        await message.author.send('❌ Guild not accessible')
        return
    
    member = guild.get_member(user_id)
    
    if member:
        # Full member info
        from utils import get_account_age, get_member_age
        
        lines = [
            f"**👤 Member Info**",
            f"**User:** {format_user(member)}",
            f"**Bot:** {'Yes 🤖' if member.bot else 'No'}",
            f"**Account Age:** {get_account_age(member)}",
            f"**Joined Server:** {get_member_age(member)}",
            f"**Nickname:** {member.nick or 'None'}",
        ]
        
        # Roles
        roles = [r.name for r in member.roles if r.name != '@everyone']
        if roles:
            lines.append(f"**Roles:** {', '.join(roles[:10])}{' ...' if len(roles) > 10 else ''}")
        else:
            lines.append("**Roles:** None")
        
        # Permissions
        perm_analysis = analyze_permissions(member.guild_permissions)
        lines.append(f"**Risk Level:** {perm_analysis['risk_level']}")
        lines.append(f"**Permissions:** {perm_analysis['summary']}")
        
        # Watched/Whitelisted status
        from db_manager import is_watched, is_whitelisted
        if is_watched(user_id):
            lines.append("**Status:** 👁️ WATCHED")
        if is_whitelisted(user_id):
            lines.append("**Status:** ✅ WHITELISTED")
        
        await message.author.send('\n'.join(lines))
    else:
        # Try to fetch user (not in guild)
        try:
            user = await bot.fetch_user(user_id)
            lines = [
                f"**👤 User Info** (Not in server)",
                f"**User:** {format_user(user)}",
                f"**Bot:** {'Yes 🤖' if user.bot else 'No'}",
                f"**Account Age:** {get_account_age(user)}",
            ]
            await message.author.send('\n'.join(lines))
        except:
            await message.author.send(f'❌ User `{user_id}` not found')

async def _cmd_logs(message: discord.Message, parts: list):
    """View user activity logs"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.logs <user_id>`')
        return
    
    user_id = parse_user_id(parts[1])
    if user_id is None:
        await message.author.send('❌ Invalid user ID')
        return
    
    db = load_db()
    audit_log = db.get('audit_log', [])
    
    # Filter logs for this user
    user_logs = [
        entry for entry in audit_log
        if entry.get('details', {}).get('user_id') == user_id
    ]
    
    if not user_logs:
        await message.author.send(f'📋 No logs found for user `{user_id}`')
        return
    
    # Show last 20 entries
    recent_logs = user_logs[-20:]
    
    lines = [f'📋 **Recent Activity for `{user_id}`** (Last {len(recent_logs)})\n']
    
    for entry in recent_logs:
        timestamp = entry.get('timestamp', 'Unknown')
        event_type = entry.get('type', 'unknown')
        from utils import get_audit_action_emoji
        emoji = get_audit_action_emoji(event_type)
        
        lines.append(f"{emoji} `{timestamp[:19]}` - {event_type}")
    
    # Split if too long
    msg = '\n'.join(lines)
    if len(msg) > 1900:
        # Send in chunks
        chunks = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
        for chunk in chunks:
            await message.author.send(chunk)
    else:
        await message.author.send(msg)

async def _cmd_stats(message: discord.Message):
    """Show bot statistics"""
    stats = get_alert_stats()
    db = load_db()
    
    lines = [
        "📊 **Q Bot Statistics**\n",
        f"**Total Alerts:** {stats.get('total_alerts', 0)}",
        f"**Bot Additions:** {stats.get('bot_additions', 0)}",
        f"**Role Changes:** {stats.get('role_changes', 0)}",
        f"**Channel Changes:** {stats.get('channel_changes', 0)}",
        f"**Bans:** {stats.get('bans', 0)}",
        f"**Kicks:** {stats.get('kicks', 0)}",
        f"\n**Watched Users:** {len(db.get('watched_users', []))}",
        f"**Whitelisted Users:** {len(db.get('whitelist', []))}",
        f"**Audit Log Entries:** {len(db.get('audit_log', []))}",
        f"**Pending Quick Actions:** {get_pending_actions_count()}"
    ]
    
    await message.author.send('\n'.join(lines))

async def _cmd_strip(message: discord.Message, parts: list, bot):
    """Strip all roles from user"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.strip <user_id>`')
        return
    
    user_id = parse_user_id(parts[1])
    if user_id is None:
        await message.author.send('❌ Invalid user ID')
        return
    
    if GUILD_ID is None:
        await message.author.send('❌ GUILD_ID not configured')
        return
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        await message.author.send('❌ Guild not accessible')
        return
    
    member = guild.get_member(user_id)
    if not member:
        await message.author.send('❌ Member not found in server')
        return
    
    # Get removable roles
    bot_member = guild.me
    to_remove = [r for r in member.roles if r != guild.default_role and r.position < bot_member.top_role.position]
    
    if not to_remove:
        await message.author.send('⚠️ No removable roles (either user has no roles or bot lacks permission)')
        return
    
    try:
        await member.remove_roles(*to_remove, reason='Roles stripped by owner via DM')
        
        add_to_audit_log('strip_roles', {
            'user_id': user_id,
            'roles_removed': [r.name for r in to_remove]
        })
        
        await message.author.send(f'✅ Stripped {len(to_remove)} roles from {member}\n**Roles:** {", ".join([r.name for r in to_remove[:10]])}')
        logger.info(f'Stripped roles from {user_id} by owner')
    except Exception as e:
        logger.exception(f'Strip failed: {e}')
        await message.author.send(f'❌ Failed to strip roles: {str(e)}')

async def _cmd_ban(message: discord.Message, parts: list, bot):
    """Ban a user"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.ban <user_id> [reason]`')
        return
    
    user_id = parse_user_id(parts[1])
    if user_id is None:
        await message.author.send('❌ Invalid user ID')
        return
    
    reason = ' '.join(parts[2:]) if len(parts) > 2 else 'Banned by owner via DM'
    
    if GUILD_ID is None:
        await message.author.send('❌ GUILD_ID not configured')
        return
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        await message.author.send('❌ Guild not accessible')
        return
    
    try:
        await guild.ban(discord.Object(id=user_id), reason=reason, delete_message_days=0)
        
        add_to_audit_log('ban_by_owner', {
            'user_id': user_id,
            'reason': reason
        })
        
        await message.author.send(f'✅ Banned user `{user_id}`\n**Reason:** {reason}')
        logger.info(f'Banned {user_id} by owner')
    except Exception as e:
        logger.exception(f'Ban failed: {e}')
        await message.author.send(f'❌ Ban failed: {str(e)}')

async def _cmd_kick(message: discord.Message, parts: list, bot):
    """Kick a user"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.kick <user_id> [reason]`')
        return
    
    user_id = parse_user_id(parts[1])
    if user_id is None:
        await message.author.send('❌ Invalid user ID')
        return
    
    reason = ' '.join(parts[2:]) if len(parts) > 2 else 'Kicked by owner via DM'
    
    if GUILD_ID is None:
        await message.author.send('❌ GUILD_ID not configured')
        return
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        await message.author.send('❌ Guild not accessible')
        return
    
    member = guild.get_member(user_id)
    if not member:
        await message.author.send('❌ Member not found in server')
        return
    
    try:
        await member.kick(reason=reason)
        
        add_to_audit_log('kick_by_owner', {
            'user_id': user_id,
            'reason': reason
        })
        
        increment_stat('kicks')
        
        await message.author.send(f'✅ Kicked {member}\n**Reason:** {reason}')
        logger.info(f'Kicked {user_id} by owner')
    except Exception as e:
        logger.exception(f'Kick failed: {e}')
        await message.author.send(f'❌ Kick failed: {str(e)}')

async def _cmd_timeout(message: discord.Message, parts: list, bot):
    """Timeout a user"""
    if len(parts) < 2:
        await message.author.send('❌ Usage: `.timeout <user_id> [minutes]`')
        return
    
    user_id = parse_user_id(parts[1])
    if user_id is None:
        await message.author.send('❌ Invalid user ID')
        return
    
    # Get duration
    try:
        duration_minutes = int(parts[2]) if len(parts) > 2 else 60
        if duration_minutes < 1 or duration_minutes > 40320:  # Max 28 days
            await message.author.send('❌ Duration must be 1-40320 minutes (28 days)')
            return
    except ValueError:
        await message.author.send('❌ Invalid duration')
        return
    
    if GUILD_ID is None:
        await message.author.send('❌ GUILD_ID not configured')
        return
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        await message.author.send('❌ Guild not accessible')
        return
    
    member = guild.get_member(user_id)
    if not member:
        await message.author.send('❌ Member not found in server')
        return
    
    try:
        duration = datetime.timedelta(minutes=duration_minutes)
        await member.timeout(duration, reason='Timeout by owner via DM')
        
        add_to_audit_log('timeout_by_owner', {
            'user_id': user_id,
            'duration_minutes': duration_minutes
        })
        
        from utils import format_duration
        await message.author.send(f'✅ Timeout applied to {member}\n**Duration:** {format_duration(duration_minutes * 60)}')
        logger.info(f'Timeout {user_id} for {duration_minutes}m by owner')
    except Exception as e:
        logger.exception(f'Timeout failed: {e}')
        await message.author.send(f'❌ Timeout failed: {str(e)}')

async def _cmd_channels(message: discord.Message, bot):
    """List all channels"""
    if GUILD_ID is None:
        await message.author.send('❌ GUILD_ID not configured')
        return
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        await message.author.send('❌ Guild not accessible')
        return
    
    lines = [f'📁 **Channels in {guild.name}**\n']
    
    # Text channels
    text_channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
    if text_channels:
        lines.append('**Text Channels:**')
        for c in text_channels[:20]:
            lines.append(f'  • #{c.name} (`{c.id}`)')
        if len(text_channels) > 20:
            lines.append(f'  ... and {len(text_channels) - 20} more')
    
    # Voice channels
    voice_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
    if voice_channels:
        lines.append('\n**Voice Channels:**')
        for c in voice_channels[:20]:
            lines.append(f'  • 🔊 {c.name} (`{c.id}`)')
        if len(voice_channels) > 20:
            lines.append(f'  ... and {len(voice_channels) - 20} more')
    
    msg = '\n'.join(lines)
    
    # Split if too long
    if len(msg) > 1900:
        chunks = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
        for chunk in chunks:
            await message.author.send(chunk)
    else:
        await message.author.send(msg)

async def _cmd_roles(message: discord.Message, bot):
    """List all roles"""
    if GUILD_ID is None:
        await message.author.send('❌ GUILD_ID not configured')
        return
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        await message.author.send('❌ Guild not accessible')
        return
    
    lines = [f'👥 **Roles in {guild.name}**\n']
    
    # Sort by position (highest first)
    roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
    
    for role in roles[:30]:
        if role.name == '@everyone':
            continue
        
        # Analyze permissions
        perm_analysis = analyze_permissions(role.permissions)
        risk = perm_analysis['risk_level']
        
        lines.append(f"{risk} **{role.name}** (`{role.id}`) - {len(role.members)} members")
    
    if len(roles) > 30:
        lines.append(f'\n... and {len(roles) - 30} more roles')
    
    msg = '\n'.join(lines)
    
    if len(msg) > 1900:
        chunks = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
        for chunk in chunks:
            await message.author.send(chunk)
    else:
        await message.author.send(msg)

async def _cmd_members(message: discord.Message, bot):
    """Show member summary"""
    if GUILD_ID is None:
        await message.author.send('❌ GUILD_ID not configured')
        return
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        await message.author.send('❌ Guild not accessible')
        return
    
    total_members = guild.member_count
    bots = len([m for m in guild.members if m.bot])
    humans = total_members - bots
    
    # Count online
    online = len([m for m in guild.members if m.status != discord.Status.offline])
    
    lines = [
        f"**👥 {guild.name} Members**\n",
        f"**Total:** {total_members}",
        f"**Humans:** {humans}",
        f"**Bots:** {bots}",
        f"**Online:** {online}"
    ]
    
    await message.author.send('\n'.join(lines))

async def _cmd_settings(message: discord.Message):
    """Show current settings"""
    from config import *
    
    lines = [
        "⚙️ **Current Settings**\n",
        f"**Bot Name:** {BOT_NAME}",
        f"**Guild ID:** {GUILD_ID or 'Not set'}",
        f"**DM Alerts:** {'✅ Enabled' if DM_ALERTS else '❌ Disabled'}",
        f"**DB Encryption:** {'✅ Enabled' if ENCRYPT_DB else '❌ Disabled'}",
        f"**Quick Actions:** {'✅ Enabled' if QUICK_ACTIONS_ENABLED else '❌ Disabled'}",
        f"**Fake Commands:** {'✅ Enabled' if ENABLE_FAKE_COMMANDS else '❌ Disabled'}",
    ]
    
    await message.author.send('\n'.join(lines))

async def _cmd_mask(message: discord.Message, parts: list, full_content: str):
    """Manage mask (auto-reply) settings"""
    if len(parts) < 2:
        await message.author.send('❌ Usage:\n  `.mask set_channel <id>`\n  `.mask set_reply <text>`\n  `.mask clear`')
        return
    
    sub = parts[1].lower()
    db = load_db()
    
    if sub == 'set_channel':
        if len(parts) < 3:
            await message.author.send('❌ Usage: `.mask set_channel <channel_id>`')
            return
        
        try:
            channel_id = int(parts[2])
        except ValueError:
            await message.author.send('❌ Invalid channel ID')
            return
        
        db['mask']['channel_id'] = str(channel_id)
        save_db(db)
        
        await message.author.send(f'✅ Mask channel set to `{channel_id}`')
        logger.info(f'Mask channel set to {channel_id} by owner')
        return
    
    if sub == 'set_reply':
        if len(parts) < 3:
            await message.author.send('❌ Usage: `.mask set_reply <text>`')
            return
        
        # Get text after "set_reply"
        text = full_content.split(None, 2)[2] if len(full_content.split(None, 2)) > 2 else ''
        
        if not text:
            await message.author.send('❌ Reply text cannot be empty')
            return
        
        db['mask']['reply_text'] = text
        save_db(db)
        
        await message.author.send(f'✅ Mask reply updated to:\n```\n{text}\n```')
        logger.info(f'Mask reply updated by owner')
        return
    
    if sub == 'clear':
        db['mask'] = {"channel_id": None, "reply_text": "━━━━━━━━━━━━"}
        save_db(db)
        
        await message.author.send('✅ Mask settings cleared')
        logger.info('Mask cleared by owner')
        return
    
    await message.author.send('❌ Unknown mask command')
