# quick_actions.py — Quick Actions Response System
import asyncio
import discord
from db_manager import load_db, save_db
from logger import logger
from config import QUICK_ACTIONS_ENABLED, QUICK_ACTION_TIMEOUT
import datetime

# Store pending quick actions: {action_id: {details}}
pending_actions = {}

def generate_action_id() -> str:
    """Generate unique action ID"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def create_quick_action(event_type: str, target_id: int, guild_id: int, details: dict) -> str:
    """
    Create a quick action and return formatted message with options
    
    Args:
        event_type: Type of event (bot_add, role_change, etc.)
        target_id: Target user/bot ID
        guild_id: Guild ID
        details: Additional details
    
    Returns:
        str: Formatted message with quick action options
    """
    if not QUICK_ACTIONS_ENABLED:
        return ""
    
    action_id = generate_action_id()
    
    # Store action
    pending_actions[action_id] = {
        'event_type': event_type,
        'target_id': target_id,
        'guild_id': guild_id,
        'details': details,
        'created_at': datetime.datetime.utcnow(),
        'expires_at': datetime.datetime.utcnow() + datetime.timedelta(seconds=QUICK_ACTION_TIMEOUT)
    }
    
    # Schedule cleanup
    asyncio.create_task(_cleanup_action(action_id))
    
    # Generate options based on event type
    options = _get_options_for_event(event_type)
    
    if not options:
        return ""
    
    # Format message
    lines = [
        f"\n{'─'*40}",
        f"⚡ **QUICK ACTIONS** [`{action_id}`]",
        f"{'─'*40}",
        "**رد برقم الإجراء المطلوب:**\n"
    ]
    
    for num, (label, command) in enumerate(options, 1):
        lines.append(f"  `{num}` → {label}")
    
    lines.append(f"\n⏰ Expires in {QUICK_ACTION_TIMEOUT//60} minutes")
    lines.append(f"{'─'*40}")
    
    return '\n'.join(lines)

def _get_options_for_event(event_type: str) -> list:
    """Get available options for event type"""
    if event_type == 'bot_add':
        return [
            ('🔨 Ban Bot', 'ban'),
            ('🗑️ Kick Bot', 'kick'),
            ('⚠️ Strip Roles', 'strip'),
            ('ℹ️ Get Info', 'info'),
            ('❌ Ignore', 'ignore')
        ]
    elif event_type == 'suspicious_member':
        return [
            ('🔨 Ban', 'ban'),
            ('⏸️ Timeout', 'timeout'),
            ('👁️ Watch', 'watch'),
            ('ℹ️ Get Info', 'info'),
            ('❌ Ignore', 'ignore')
        ]
    elif event_type == 'role_change':
        return [
            ('⚠️ Strip Roles', 'strip'),
            ('ℹ️ Get Info', 'info'),
            ('❌ Ignore', 'ignore')
        ]
    else:
        return []

async def _cleanup_action(action_id: str):
    """Remove expired action after timeout"""
    await asyncio.sleep(QUICK_ACTION_TIMEOUT)
    if action_id in pending_actions:
        del pending_actions[action_id]
        logger.debug(f'Quick action {action_id} expired')

async def handle_quick_action_response(bot, message: discord.Message, action_id: str, choice: int) -> str:
    """
    Handle user's quick action choice
    
    Args:
        bot: Bot instance
        message: User's DM message
        action_id: Action ID
        choice: User's numeric choice
    
    Returns:
        str: Response message
    """
    # Validate action exists
    if action_id not in pending_actions:
        return '❌ Action expired or not found'
    
    action = pending_actions[action_id]
    
    # Check if expired
    if datetime.datetime.utcnow() > action['expires_at']:
        del pending_actions[action_id]
        return '❌ Action expired'
    
    # Get options
    options = _get_options_for_event(action['event_type'])
    
    if choice < 1 or choice > len(options):
        return f'❌ Invalid choice. Pick 1-{len(options)}'
    
    # Get selected action
    label, command = options[choice - 1]
    
    # Execute action
    result = await _execute_action(bot, action, command)
    
    # Clean up
    del pending_actions[action_id]
    
    return f'✅ **{label}**\n{result}'

async def _execute_action(bot, action: dict, command: str) -> str:
    """Execute the quick action command"""
    try:
        guild = bot.get_guild(action['guild_id'])
        if not guild:
            return '❌ Guild not found'
        
        target_id = action['target_id']
        
        if command == 'ban':
            try:
                await guild.ban(discord.Object(id=target_id), reason='Quick action: Ban')
                logger.info(f'Quick action: Banned {target_id}')
                return f'✅ Banned user {target_id}'
            except Exception as e:
                logger.exception(f'Quick ban failed: {e}')
                return f'❌ Ban failed: {str(e)}'
        
        elif command == 'kick':
            try:
                member = guild.get_member(target_id)
                if member:
                    await member.kick(reason='Quick action: Kick')
                    logger.info(f'Quick action: Kicked {target_id}')
                    return f'✅ Kicked user {target_id}'
                else:
                    return '❌ Member not found'
            except Exception as e:
                logger.exception(f'Quick kick failed: {e}')
                return f'❌ Kick failed: {str(e)}'
        
        elif command == 'strip':
            try:
                member = guild.get_member(target_id)
                if not member:
                    return '❌ Member not found'
                
                bot_member = guild.me
                to_remove = [r for r in member.roles if r != guild.default_role and r.position < bot_member.top_role.position]
                
                if to_remove:
                    await member.remove_roles(*to_remove, reason='Quick action: Strip')
                    logger.info(f'Quick action: Stripped roles from {target_id}')
                    return f'✅ Stripped {len(to_remove)} roles from {target_id}'
                else:
                    return '⚠️ No removable roles'
            except Exception as e:
                logger.exception(f'Quick strip failed: {e}')
                return f'❌ Strip failed: {str(e)}'
        
        elif command == 'timeout':
            try:
                member = guild.get_member(target_id)
                if not member:
                    return '❌ Member not found'
                
                import datetime
                await member.timeout(datetime.timedelta(hours=1), reason='Quick action: Timeout')
                logger.info(f'Quick action: Timeout {target_id}')
                return f'✅ Timeout applied to {target_id} (1 hour)'
            except Exception as e:
                logger.exception(f'Quick timeout failed: {e}')
                return f'❌ Timeout failed: {str(e)}'
        
        elif command == 'watch':
            from db_manager import load_db, save_db
            db = load_db()
            user_id_str = str(target_id)
            if user_id_str not in db.get('watched_users', []):
                db.setdefault('watched_users', []).append(user_id_str)
                save_db(db)
                logger.info(f'Quick action: Now watching {target_id}')
                return f'✅ Now watching {target_id}'
            else:
                return f'⚠️ Already watching {target_id}'
        
        elif command == 'info':
            member = guild.get_member(target_id)
            if not member:
                return f'❌ Member not found (ID: {target_id})'
            
            info_lines = [
                f'**User:** {member} ({member.id})',
                f'**Created:** {member.created_at.strftime("%Y-%m-%d %H:%M")}',
                f'**Joined:** {member.joined_at.strftime("%Y-%m-%d %H:%M") if member.joined_at else "Unknown"}',
                f'**Roles:** {", ".join([r.name for r in member.roles if r.name != "@everyone"]) or "None"}',
                f'**Is Bot:** {"Yes" if member.bot else "No"}'
            ]
            return '\n'.join(info_lines)
        
        elif command == 'ignore':
            return '✅ Ignored'
        
        else:
            return '❌ Unknown command'
    
    except Exception as e:
        logger.exception(f'Execute action failed: {e}')
        return f'❌ Action failed: {str(e)}'

def get_pending_actions_count() -> int:
    """Get count of pending quick actions"""
    return len(pending_actions)

def clear_expired_actions():
    """Manually clear all expired actions"""
    now = datetime.datetime.utcnow()
    expired = [aid for aid, action in pending_actions.items() if now > action['expires_at']]
    for aid in expired:
        del pending_actions[aid]
    return len(expired)
