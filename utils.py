# utils.py — Utility Functions
import discord
from datetime import datetime, timedelta

def get_color_for_priority(priority: str) -> discord.Color:
    """Get embed color based on priority"""
    if '🔴' in priority or 'CRITICAL' in priority:
        return discord.Color.red()
    elif '🟡' in priority or 'WARNING' in priority:
        return discord.Color.gold()
    elif '🟢' in priority or 'INFO' in priority:
        return discord.Color.green()
    else:
        return discord.Color.blue()

def format_timestamp(dt: datetime = None) -> str:
    """Format datetime for display"""
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

def format_user(user: discord.User or discord.Member) -> str:
    """Format user for display"""
    return f"{user} ({user.id})"

def format_channel(channel: discord.abc.GuildChannel) -> str:
    """Format channel for display"""
    return f"#{channel.name} ({channel.id})"

def format_role(role: discord.Role) -> str:
    """Format role for display"""
    return f"@{role.name} ({role.id})"

def get_account_age(user: discord.User) -> str:
    """Get account age description"""
    age = datetime.utcnow() - user.created_at.replace(tzinfo=None)
    
    if age < timedelta(days=1):
        return f"⚠️ {age.seconds // 3600} hours old (NEW!)"
    elif age < timedelta(days=7):
        return f"⚠️ {age.days} days old (RECENT)"
    elif age < timedelta(days=30):
        return f"{age.days} days old"
    elif age < timedelta(days=365):
        return f"{age.days // 30} months old"
    else:
        return f"{age.days // 365} years old"

def get_member_age(member: discord.Member) -> str:
    """Get member join age"""
    if not member.joined_at:
        return "Unknown"
    
    age = datetime.utcnow() - member.joined_at.replace(tzinfo=None)
    
    if age < timedelta(hours=1):
        return f"⚠️ {age.seconds // 60} minutes ago (JUST JOINED!)"
    elif age < timedelta(days=1):
        return f"⚠️ {age.seconds // 3600} hours ago"
    elif age < timedelta(days=7):
        return f"{age.days} days ago"
    elif age < timedelta(days=30):
        return f"{age.days} days ago"
    else:
        return f"{age.days // 30} months ago"

def is_suspicious_account(user: discord.User) -> tuple[bool, str]:
    """
    Check if account is suspicious
    
    Returns:
        tuple: (is_suspicious, reason)
    """
    age = datetime.utcnow() - user.created_at.replace(tzinfo=None)
    
    # Less than 7 days old
    if age < timedelta(days=7):
        return True, f"New account ({age.days} days old)"
    
    # Default avatar (no custom avatar)
    if user.avatar is None:
        return True, "No custom avatar"
    
    return False, "OK"

def format_permissions(perms: discord.Permissions) -> str:
    """Format permissions for display"""
    if perms.administrator:
        return "🔴 **ADMINISTRATOR**"
    
    sensitive = []
    if perms.manage_guild:
        sensitive.append("Manage Server")
    if perms.manage_roles:
        sensitive.append("Manage Roles")
    if perms.manage_channels:
        sensitive.append("Manage Channels")
    if perms.ban_members:
        sensitive.append("Ban Members")
    if perms.kick_members:
        sensitive.append("Kick Members")
    if perms.manage_webhooks:
        sensitive.append("Manage Webhooks")
    if perms.manage_messages:
        sensitive.append("Manage Messages")
    if perms.mention_everyone:
        sensitive.append("Mention Everyone")
    
    if sensitive:
        return "⚠️ " + ", ".join(sensitive)
    else:
        return "✅ No sensitive permissions"

def truncate_text(text: str, max_length: int = 1024) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_list(items: list, max_items: int = 10) -> str:
    """Format list with limit"""
    if not items:
        return "None"
    
    if len(items) <= max_items:
        return ", ".join(items)
    
    visible = items[:max_items]
    remaining = len(items) - max_items
    return ", ".join(visible) + f" ... and {remaining} more"

def get_audit_action_emoji(action: str) -> str:
    """Get emoji for audit action type"""
    emoji_map = {
        'member_join': '📥',
        'member_leave': '📤',
        'member_ban': '🔨',
        'member_unban': '🔓',
        'member_kick': '👢',
        'member_update': '✏️',
        'bot_add': '🤖',
        'role_create': '➕',
        'role_delete': '➖',
        'role_update': '✏️',
        'channel_create': '📁',
        'channel_delete': '🗑️',
        'channel_update': '✏️',
        'message_delete': '❌',
        'message_edit': '✏️',
        'webhook_create': '🔗',
        'webhook_delete': '⛓️',
    }
    return emoji_map.get(action, '📋')

def parse_user_id(text: str) -> int:
    """
    Parse user ID from text (handles mentions and plain IDs)
    
    Returns:
        int: User ID or None if invalid
    """
    # Remove mention format <@123> or <@!123>
    text = text.strip()
    if text.startswith('<@') and text.endswith('>'):
        text = text[2:-1]
        if text.startswith('!'):
            text = text[1:]
    
    try:
        return int(text)
    except ValueError:
        return None

def format_duration(seconds: int) -> str:
    """Format seconds into human readable duration"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"
