# permissions.py — Ultimate Permission Analysis System
import discord
from utils import format_permissions

# Critical permissions that require immediate alert
CRITICAL_PERMS = [
    'administrator',
    'manage_guild',
    'manage_roles',
]

# Dangerous permissions that require monitoring
DANGEROUS_PERMS = [
    'manage_channels',
    'manage_webhooks',
    'ban_members',
    'kick_members',
    'manage_messages',
    'mention_everyone',
    'manage_nicknames',
    'manage_emojis',
]

# Moderate permissions
MODERATE_PERMS = [
    'create_instant_invite',
    'view_audit_log',
    'priority_speaker',
    'move_members',
    'mute_members',
    'deafen_members',
]

def analyze_permissions(perms: discord.Permissions) -> dict:
    """
    Analyze permissions and categorize them
    
    Returns:
        dict: {
            'has_critical': bool,
            'has_dangerous': bool,
            'critical_list': list,
            'dangerous_list': list,
            'moderate_list': list,
            'risk_level': str,
            'summary': str
        }
    """
    critical_found = []
    dangerous_found = []
    moderate_found = []
    
    # Check critical
    for perm in CRITICAL_PERMS:
        if getattr(perms, perm, False):
            critical_found.append(perm.replace('_', ' ').title())
    
    # Check dangerous
    for perm in DANGEROUS_PERMS:
        if getattr(perms, perm, False):
            dangerous_found.append(perm.replace('_', ' ').title())
    
    # Check moderate
    for perm in MODERATE_PERMS:
        if getattr(perms, perm, False):
            moderate_found.append(perm.replace('_', ' ').title())
    
    # Determine risk level
    if critical_found:
        risk_level = '🔴 CRITICAL'
    elif dangerous_found:
        risk_level = '🟡 HIGH'
    elif moderate_found:
        risk_level = '🟠 MODERATE'
    else:
        risk_level = '🟢 LOW'
    
    # Generate summary
    summary = format_permissions(perms)
    
    return {
        'has_critical': bool(critical_found),
        'has_dangerous': bool(dangerous_found),
        'critical_list': critical_found,
        'dangerous_list': dangerous_found,
        'moderate_list': moderate_found,
        'risk_level': risk_level,
        'summary': summary
    }

def get_permission_changes(before: discord.Permissions, after: discord.Permissions) -> dict:
    """
    Get changes between two permission sets
    
    Returns:
        dict: {
            'added': list of permission names,
            'removed': list of permission names,
            'has_critical_changes': bool
        }
    """
    added = []
    removed = []
    
    # Get all permission names
    all_perms = [attr for attr in dir(before) if not attr.startswith('_') and isinstance(getattr(before, attr), bool)]
    
    for perm in all_perms:
        before_val = getattr(before, perm, False)
        after_val = getattr(after, perm, False)
        
        if before_val != after_val:
            perm_name = perm.replace('_', ' ').title()
            if after_val:  # Permission added
                added.append(perm_name)
            else:  # Permission removed
                removed.append(perm_name)
    
    # Check if critical permissions changed
    has_critical = any(perm.replace(' ', '_').lower() in CRITICAL_PERMS for perm in added + removed)
    
    return {
        'added': added,
        'removed': removed,
        'has_critical_changes': has_critical
    }

def role_list(member: discord.Member, include_everyone: bool = False) -> str:
    """Get formatted role list for member"""
    roles = [r.name for r in member.roles if include_everyone or r.name != '@everyone']
    if not roles:
        return 'None'
    return ', '.join(roles)

def get_highest_role_position(member: discord.Member) -> int:
    """Get highest role position for member"""
    if not member.roles:
        return 0
    return max(r.position for r in member.roles)

def can_manage_member(bot_member: discord.Member, target_member: discord.Member) -> bool:
    """Check if bot can manage target member"""
    return bot_member.top_role.position > target_member.top_role.position

def get_dangerous_roles(guild: discord.Guild, threshold: str = 'dangerous') -> list:
    """
    Get list of roles with dangerous permissions
    
    Args:
        guild: Guild to check
        threshold: 'critical', 'dangerous', or 'moderate'
    
    Returns:
        list: List of (role, risk_level) tuples
    """
    dangerous_roles = []
    
    for role in guild.roles:
        if role.name == '@everyone':
            continue
        
        analysis = analyze_permissions(role.permissions)
        
        if threshold == 'critical' and analysis['has_critical']:
            dangerous_roles.append((role, analysis['risk_level']))
        elif threshold == 'dangerous' and (analysis['has_critical'] or analysis['has_dangerous']):
            dangerous_roles.append((role, analysis['risk_level']))
        elif threshold == 'moderate':
            if analysis['has_critical'] or analysis['has_dangerous'] or analysis['moderate_list']:
                dangerous_roles.append((role, analysis['risk_level']))
    
    return dangerous_roles

def format_role_info(role: discord.Role) -> str:
    """Get detailed role information"""
    analysis = analyze_permissions(role.permissions)
    
    lines = [
        f"**Role:** {role.name}",
        f"**ID:** {role.id}",
        f"**Position:** {role.position}",
        f"**Color:** {role.color}",
        f"**Mentionable:** {'Yes' if role.mentionable else 'No'}",
        f"**Hoisted:** {'Yes' if role.hoist else 'No'}",
        f"**Members:** {len(role.members)}",
        f"**Risk Level:** {analysis['risk_level']}",
        f"**Permissions:** {analysis['summary']}"
    ]
    
    if analysis['critical_list']:
        lines.append(f"**🔴 Critical Perms:** {', '.join(analysis['critical_list'])}")
    if analysis['dangerous_list']:
        lines.append(f"**🟡 Dangerous Perms:** {', '.join(analysis['dangerous_list'])}")
    
    return '\n'.join(lines)

def check_member_can_harm(member: discord.Member) -> tuple[bool, str]:
    """
    Check if member has permissions that could harm server
    
    Returns:
        tuple: (can_harm, reason)
    """
    analysis = analyze_permissions(member.guild_permissions)
    
    if analysis['has_critical']:
        return True, f"Has CRITICAL permissions: {', '.join(analysis['critical_list'])}"
    
    if analysis['has_dangerous']:
        return True, f"Has DANGEROUS permissions: {', '.join(analysis['dangerous_list'])}"
    
    return False, "No harmful permissions"
