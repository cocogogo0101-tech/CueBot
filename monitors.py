# monitors.py — ULTIMATE Server Monitoring System
import discord
from logger import logger
from dm_notify import alert, alert_critical, alert_warning, alert_info
from db_manager import add_to_audit_log, increment_stat, is_watched, is_whitelisted
from filters import should_alert, get_priority
from permissions import analyze_permissions, format_role_info, check_member_can_harm
from quick_actions import create_quick_action
from utils import *
from config import GUILD_ID

# ============= BOT ADDITION MONITOR =============
async def handle_member_join(bot, member: discord.Member):
    """Monitor when members/bots join"""
    try:
        # Skip if not our guild
        if GUILD_ID and member.guild.id != GUILD_ID:
            return
        
        # Check if whitelisted
        if is_whitelisted(member.id):
            logger.debug(f'Whitelisted member joined: {member.id}')
            return
        
        # BOT ADDITION - CRITICAL!
        if member.bot:
            await _handle_bot_addition(bot, member)
            return
        
        # Regular member join
        if should_alert('members', member.id):
            await _handle_regular_member_join(bot, member)
    
    except Exception as e:
        logger.exception(f'handle_member_join failed: {e}')

async def _handle_bot_addition(bot, member: discord.Member):
    """Handle bot addition (CRITICAL EVENT)"""
    try:
        guild = member.guild
        details_lines = [
            f"**Bot:** {format_user(member)}",
            f"**Account Age:** {get_account_age(member)}",
            f"**Added to:** {guild.name} ({guild.id})"
        ]
        
        # Get who added the bot (from audit log)
        adder = None
        try:
            async for entry in guild.audit_logs(limit=20, action=discord.AuditLogAction.bot_add):
                if entry.target and entry.target.id == member.id:
                    adder = entry.user
                    details_lines.append(f"**Added by:** {format_user(adder)}")
                    break
        except Exception as e:
            logger.warning(f'Could not read audit log: {e}')
            details_lines.append("**Added by:** Unknown (no audit log access)")
        
        # Analyze permissions
        perm_analysis = analyze_permissions(member.guild_permissions)
        details_lines.append(f"**Risk Level:** {perm_analysis['risk_level']}")
        details_lines.append(f"**Permissions:** {perm_analysis['summary']}")
        
        # Check assigned roles
        roles = [r.name for r in member.roles if r.name != '@everyone']
        if roles:
            details_lines.append(f"**Roles:** {', '.join(roles)}")
        else:
            details_lines.append("**Roles:** None")
        
        # Add to audit log
        add_to_audit_log('bot_add', {
            'bot_id': member.id,
            'bot_name': str(member),
            'adder_id': adder.id if adder else None,
            'adder_name': str(adder) if adder else None,
            'risk_level': perm_analysis['risk_level'],
            'permissions': perm_analysis['summary']
        })
        
        increment_stat('bot_additions')
        
        # Create quick action
        quick_action_text = create_quick_action(
            'bot_add',
            member.id,
            guild.id,
            {'bot_name': str(member), 'adder': str(adder) if adder else 'Unknown'}
        )
        
        # Send critical alert
        await alert_critical(
            bot,
            "BOT ADDED TO SERVER",
            '\n'.join(details_lines),
            quick_action_text=quick_action_text
        )
        
        logger.info(f'Bot added alert sent: {member.id}')
    
    except Exception as e:
        logger.exception(f'_handle_bot_addition failed: {e}')

async def _handle_regular_member_join(bot, member: discord.Member):
    """Handle regular member join"""
    try:
        # Check if account is suspicious
        is_sus, reason = is_suspicious_account(member)
        
        if is_sus or is_watched(member.id):
            details_lines = [
                f"**Member:** {format_user(member)}",
                f"**Account Age:** {get_account_age(member)}",
                f"**Guild:** {member.guild.name}"
            ]
            
            if is_sus:
                details_lines.append(f"**⚠️ Suspicious:** {reason}")
            
            if is_watched(member.id):
                details_lines.append("**👁️ WATCHED USER!**")
            
            # Add to audit log
            add_to_audit_log('member_join', {
                'user_id': member.id,
                'user_name': str(member),
                'suspicious': is_sus,
                'reason': reason if is_sus else None,
                'watched': is_watched(member.id)
            })
            
            priority = '🟡 WARNING' if is_sus or is_watched(member.id) else '🟢 INFO'
            
            await alert(
                bot,
                "Member Joined",
                '\n'.join(details_lines),
                priority=priority
            )
    
    except Exception as e:
        logger.exception(f'_handle_regular_member_join failed: {e}')

# ============= MEMBER LEAVE MONITOR =============
async def handle_member_remove(bot, member: discord.Member):
    """Monitor when members leave"""
    try:
        if GUILD_ID and member.guild.id != GUILD_ID:
            return
        
        # Only alert for watched users or bots
        if is_watched(member.id) or member.bot:
            details = f"**{'Bot' if member.bot else 'Member'}:** {format_user(member)}\n**Guild:** {member.guild.name}"
            
            add_to_audit_log('member_leave', {
                'user_id': member.id,
                'user_name': str(member),
                'was_bot': member.bot
            })
            
            if should_alert('members', member.id):
                await alert_info(bot, "Member Left", details)
    
    except Exception as e:
        logger.exception(f'handle_member_remove failed: {e}')

# ============= MEMBER UPDATE MONITOR =============
async def handle_member_update(bot, before: discord.Member, after: discord.Member):
    """Monitor member updates (roles, nickname, etc.)"""
    try:
        if GUILD_ID and after.guild.id != GUILD_ID:
            return
        
        # Only alert for watched users or significant changes
        if not (is_watched(after.id) or should_alert('members', after.id)):
            return
        
        changes = []
        
        # Check nickname change
        if before.nick != after.nick:
            changes.append(f"**Nickname:** `{before.nick or 'None'}` → `{after.nick or 'None'}`")
        
        # Check role changes
        before_roles = set(before.roles)
        after_roles = set(after.roles)
        
        added_roles = after_roles - before_roles
        removed_roles = before_roles - after_roles
        
        if added_roles:
            role_names = [r.name for r in added_roles]
            changes.append(f"**Roles Added:** {', '.join(role_names)}")
        
        if removed_roles:
            role_names = [r.name for r in removed_roles]
            changes.append(f"**Roles Removed:** {', '.join(role_names)}")
        
        # Check permission changes
        if before.guild_permissions != after.guild_permissions:
            from permissions import get_permission_changes
            perm_changes = get_permission_changes(before.guild_permissions, after.guild_permissions)
            
            if perm_changes['added']:
                changes.append(f"**Permissions Added:** {', '.join(perm_changes['added'][:5])}")
            if perm_changes['removed']:
                changes.append(f"**Permissions Removed:** {', '.join(perm_changes['removed'][:5])}")
        
        if changes:
            details_lines = [
                f"**Member:** {format_user(after)}",
                *changes
            ]
            
            add_to_audit_log('member_update', {
                'user_id': after.id,
                'user_name': str(after),
                'changes': changes
            })
            
            # Check if changes are critical
            is_critical = any('Administrator' in str(c) or 'Manage' in str(c) for c in changes)
            priority = '🔴 CRITICAL' if is_critical else '🟡 WARNING'
            
            await alert(
                bot,
                "Member Updated",
                '\n'.join(details_lines),
                priority=priority
            )
    
    except Exception as e:
        logger.exception(f'handle_member_update failed: {e}')

# ============= BAN/KICK MONITOR =============
async def handle_member_ban(bot, guild: discord.Guild, user: discord.User):
    """Monitor member bans"""
    try:
        if GUILD_ID and guild.id != GUILD_ID:
            return
        
        details_lines = [
            f"**User:** {format_user(user)}",
            f"**Guild:** {guild.name}"
        ]
        
        # Try to get who banned
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                if entry.target and entry.target.id == user.id:
                    details_lines.append(f"**Banned by:** {format_user(entry.user)}")
                    if entry.reason:
                        details_lines.append(f"**Reason:** {entry.reason}")
                    break
        except:
            pass
        
        add_to_audit_log('member_ban', {
            'user_id': user.id,
            'user_name': str(user),
            'guild_id': guild.id
        })
        
        increment_stat('bans')
        
        if should_alert('moderation', user.id):
            await alert_warning(
                bot,
                "Member Banned",
                '\n'.join(details_lines)
            )
    
    except Exception as e:
        logger.exception(f'handle_member_ban failed: {e}')

async def handle_member_unban(bot, guild: discord.Guild, user: discord.User):
    """Monitor member unbans"""
    try:
        if GUILD_ID and guild.id != GUILD_ID:
            return
        
        details = f"**User:** {format_user(user)}\n**Guild:** {guild.name}"
        
        add_to_audit_log('member_unban', {
            'user_id': user.id,
            'user_name': str(user)
        })
        
        if should_alert('moderation', user.id):
            await alert_info(bot, "Member Unbanned", details)
    
    except Exception as e:
        logger.exception(f'handle_member_unban failed: {e}')

# ============= CHANNEL MONITOR =============
async def handle_channel_create(bot, channel: discord.abc.GuildChannel):
    """Monitor channel creation"""
    try:
        if GUILD_ID and channel.guild.id != GUILD_ID:
            return
        
        details_lines = [
            f"**Channel:** {format_channel(channel)}",
            f"**Type:** {type(channel).__name__}",
            f"**Category:** {channel.category.name if channel.category else 'None'}"
        ]
        
        # Try to get who created it
        try:
            async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_create):
                if entry.target and entry.target.id == channel.id:
                    details_lines.append(f"**Created by:** {format_user(entry.user)}")
                    break
        except:
            pass
        
        add_to_audit_log('channel_create', {
            'channel_id': channel.id,
            'channel_name': channel.name,
            'channel_type': type(channel).__name__
        })
        
        increment_stat('channel_changes')
        
        if should_alert('channels'):
            await alert_info(
                bot,
                "Channel Created",
                '\n'.join(details_lines)
            )
    
    except Exception as e:
        logger.exception(f'handle_channel_create failed: {e}')

async def handle_channel_delete(bot, channel: discord.abc.GuildChannel):
    """Monitor channel deletion"""
    try:
        if GUILD_ID and channel.guild.id != GUILD_ID:
            return
        
        details_lines = [
            f"**Channel:** {format_channel(channel)}",
            f"**Type:** {type(channel).__name__}"
        ]
        
        # Try to get who deleted it
        try:
            async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
                if entry.target and entry.target.id == channel.id:
                    details_lines.append(f"**Deleted by:** {format_user(entry.user)}")
                    break
        except:
            pass
        
        add_to_audit_log('channel_delete', {
            'channel_id': channel.id,
            'channel_name': channel.name
        })
        
        increment_stat('channel_changes')
        
        if should_alert('channels'):
            await alert_warning(
                bot,
                "Channel Deleted",
                '\n'.join(details_lines)
            )
    
    except Exception as e:
        logger.exception(f'handle_channel_delete failed: {e}')

async def handle_channel_update(bot, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
    """Monitor channel updates"""
    try:
        if GUILD_ID and after.guild.id != GUILD_ID:
            return
        
        if not should_alert('channels'):
            return
        
        changes = []
        
        # Name change
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")
        
        # Category change
        if hasattr(before, 'category') and before.category != after.category:
            before_cat = before.category.name if before.category else 'None'
            after_cat = after.category.name if after.category else 'None'
            changes.append(f"**Category:** `{before_cat}` → `{after_cat}`")
        
        # Permission changes (basic check)
        if hasattr(before, 'overwrites') and before.overwrites != after.overwrites:
            changes.append("**Permissions:** Modified")
        
        if changes:
            details_lines = [
                f"**Channel:** {format_channel(after)}",
                *changes
            ]
            
            add_to_audit_log('channel_update', {
                'channel_id': after.id,
                'changes': changes
            })
            
            await alert_info(
                bot,
                "Channel Updated",
                '\n'.join(details_lines)
            )
    
    except Exception as e:
        logger.exception(f'handle_channel_update failed: {e}')

# ============= ROLE MONITOR =============
async def handle_guild_role_create(bot, role: discord.Role):
    """Monitor role creation"""
    try:
        if GUILD_ID and role.guild.id != GUILD_ID:
            return
        
        perm_analysis = analyze_permissions(role.permissions)
        
        details_lines = [
            f"**Role:** {format_role(role)}",
            f"**Color:** {role.color}",
            f"**Position:** {role.position}",
            f"**Risk Level:** {perm_analysis['risk_level']}",
            f"**Permissions:** {perm_analysis['summary']}"
        ]
        
        # Try to get who created it
        try:
            async for entry in role.guild.audit_logs(limit=5, action=discord.AuditLogAction.role_create):
                if entry.target and entry.target.id == role.id:
                    details_lines.append(f"**Created by:** {format_user(entry.user)}")
                    break
        except:
            pass
        
        add_to_audit_log('role_create', {
            'role_id': role.id,
            'role_name': role.name,
            'risk_level': perm_analysis['risk_level']
        })
        
        increment_stat('role_changes')
        
        if should_alert('roles'):
            priority = '🔴 CRITICAL' if perm_analysis['has_critical'] else '🟡 WARNING'
            await alert(
                bot,
                "Role Created",
                '\n'.join(details_lines),
                priority=priority
            )
    
    except Exception as e:
        logger.exception(f'handle_guild_role_create failed: {e}')

async def handle_guild_role_delete(bot, role: discord.Role):
    """Monitor role deletion"""
    try:
        if GUILD_ID and role.guild.id != GUILD_ID:
            return
        
        details = f"**Role:** {format_role(role)}\n**Had {len(role.members)} members**"
        
        add_to_audit_log('role_delete', {
            'role_id': role.id,
            'role_name': role.name
        })
        
        increment_stat('role_changes')
        
        if should_alert('roles'):
            await alert_warning(bot, "Role Deleted", details)
    
    except Exception as e:
        logger.exception(f'handle_guild_role_delete failed: {e}')

async def handle_guild_role_update(bot, before: discord.Role, after: discord.Role):
    """Monitor role updates"""
    try:
        if GUILD_ID and after.guild.id != GUILD_ID:
            return
        
        if not should_alert('roles'):
            return
        
        changes = []
        
        # Name change
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")
        
        # Permission changes
        if before.permissions != after.permissions:
            from permissions import get_permission_changes
            perm_changes = get_permission_changes(before.permissions, after.permissions)
            
            if perm_changes['added']:
                changes.append(f"**➕ Permissions Added:** {', '.join(perm_changes['added'][:5])}")
            if perm_changes['removed']:
                changes.append(f"**➖ Permissions Removed:** {', '.join(perm_changes['removed'][:5])}")
        
        # Color change
        if before.color != after.color:
            changes.append(f"**Color:** Changed")
        
        if changes:
            perm_analysis = analyze_permissions(after.permissions)
            
            details_lines = [
                f"**Role:** {format_role(after)}",
                f"**Risk Level:** {perm_analysis['risk_level']}",
                *changes
            ]
            
            add_to_audit_log('role_update', {
                'role_id': after.id,
                'changes': changes
            })
            
            is_critical = any('Administrator' in str(c) or 'Manage' in str(c) for c in changes)
            priority = '🔴 CRITICAL' if is_critical else '🟡 WARNING'
            
            await alert(
                bot,
                "Role Updated",
                '\n'.join(details_lines),
                priority=priority
            )
    
    except Exception as e:
        logger.exception(f'handle_guild_role_update failed: {e}')

# ============= MESSAGE MONITOR (For watched users only) =============
async def handle_message_delete(bot, message: discord.Message):
    """Monitor message deletions (watched users only)"""
    try:
        if message.guild is None:
            return
        
        if GUILD_ID and message.guild.id != GUILD_ID:
            return
        
        # Only track watched users
        if not is_watched(message.author.id):
            return
        
        if not should_alert('messages', message.author.id):
            return
        
        content_preview = truncate_text(message.content, 200) if message.content else "[No text content]"
        
        details_lines = [
            f"**Author:** {format_user(message.author)} 👁️",
            f"**Channel:** {format_channel(message.channel)}",
            f"**Content:** ```{content_preview}```"
        ]
        
        if message.attachments:
            details_lines.append(f"**Attachments:** {len(message.attachments)} file(s)")
        
        add_to_audit_log('message_delete', {
            'user_id': message.author.id,
            'channel_id': message.channel.id,
            'content': message.content[:500]
        })
        
        await alert_info(
            bot,
            "Message Deleted (Watched User)",
            '\n'.join(details_lines)
        )
    
    except Exception as e:
        logger.exception(f'handle_message_delete failed: {e}')

async def handle_message_edit(bot, before: discord.Message, after: discord.Message):
    """Monitor message edits (watched users only)"""
    try:
        if after.guild is None:
            return
        
        if GUILD_ID and after.guild.id != GUILD_ID:
            return
        
        # Only track watched users
        if not is_watched(after.author.id):
            return
        
        if not should_alert('messages', after.author.id):
            return
        
        # Ignore embed updates
        if before.content == after.content:
            return
        
        before_preview = truncate_text(before.content, 150) if before.content else "[Empty]"
        after_preview = truncate_text(after.content, 150) if after.content else "[Empty]"
        
        details_lines = [
            f"**Author:** {format_user(after.author)} 👁️",
            f"**Channel:** {format_channel(after.channel)}",
            f"**Before:** ```{before_preview}```",
            f"**After:** ```{after_preview}```"
        ]
        
        add_to_audit_log('message_edit', {
            'user_id': after.author.id,
            'channel_id': after.channel.id,
            'before': before.content[:500],
            'after': after.content[:500]
        })
        
        await alert_info(
            bot,
            "Message Edited (Watched User)",
            '\n'.join(details_lines)
        )
    
    except Exception as e:
        logger.exception(f'handle_message_edit failed: {e}')

# ============= GUILD UPDATE MONITOR =============
async def handle_guild_update(bot, before: discord.Guild, after: discord.Guild):
    """Monitor server settings changes"""
    try:
        if GUILD_ID and after.id != GUILD_ID:
            return
        
        if not should_alert('server'):
            return
        
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")
        
        if before.icon != after.icon:
            changes.append("**Icon:** Changed")
        
        if before.verification_level != after.verification_level:
            changes.append(f"**Verification:** {before.verification_level} → {after.verification_level}")
        
        if before.default_notifications != after.default_notifications:
            changes.append(f"**Notifications:** Changed")
        
        if changes:
            add_to_audit_log('guild_update', {'changes': changes})
            
            await alert_warning(
                bot,
                "Server Settings Changed",
                '\n'.join(changes)
            )
    
    except Exception as e:
        logger.exception(f'handle_guild_update failed: {e}')

# ============= VOICE MONITOR =============
async def handle_voice_state_update(bot, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Monitor voice channel activity"""
    try:
        if GUILD_ID and member.guild.id != GUILD_ID:
            return
        
        # Only alert for watched users
        if not is_watched(member.id):
            return
        
        if not should_alert('voice', member.id):
            return
        
        # Joined voice
        if before.channel is None and after.channel is not None:
            details = f"**User:** {format_user(member)} 👁️\n**Joined:** {after.channel.name}"
            await alert_info(bot, "Voice: Joined", details)
        
        # Left voice
        elif before.channel is not None and after.channel is None:
            details = f"**User:** {format_user(member)} 👁️\n**Left:** {before.channel.name}"
            await alert_info(bot, "Voice: Left", details)
        
        # Moved channels
        elif before.channel != after.channel:
            details = f"**User:** {format_user(member)} 👁️\n**From:** {before.channel.name}\n**To:** {after.channel.name}"
            await alert_info(bot, "Voice: Moved", details)
    
    except Exception as e:
        logger.exception(f'handle_voice_state_update failed: {e}')

# ============= INVITE TRACKER =============
# Store invites on bot ready
_invite_cache = {}

async def cache_invites(guild: discord.Guild):
    """Cache current invites"""
    try:
        invites = await guild.invites()
        _invite_cache[guild.id] = {inv.code: inv.uses for inv in invites}
        logger.info(f'Cached {len(invites)} invites for guild {guild.id}')
    except Exception as e:
        logger.warning(f'Could not cache invites: {e}')

async def handle_invite_create(bot, invite: discord.Invite):
    """Monitor invite creation"""
    try:
        if GUILD_ID and invite.guild.id != GUILD_ID:
            return
        
        if not should_alert('invites'):
            return
        
        # Update cache
        if invite.guild.id not in _invite_cache:
            _invite_cache[invite.guild.id] = {}
        _invite_cache[invite.guild.id][invite.code] = 0
        
        details_lines = [
            f"**Code:** {invite.code}",
            f"**Channel:** {invite.channel.name}",
            f"**Inviter:** {format_user(invite.inviter) if invite.inviter else 'Unknown'}",
            f"**Max Uses:** {invite.max_uses or 'Unlimited'}",
            f"**Expires:** {format_duration(invite.max_age) if invite.max_age else 'Never'}"
        ]
        
        await alert_info(
            bot,
            "Invite Created",
            '\n'.join(details_lines)
        )
    
    except Exception as e:
        logger.exception(f'handle_invite_create failed: {e}')

async def handle_invite_delete(bot, invite: discord.Invite):
    """Monitor invite deletion"""
    try:
        if GUILD_ID and invite.guild.id != GUILD_ID:
            return
        
        if not should_alert('invites'):
            return
        
        # Remove from cache
        if invite.guild.id in _invite_cache and invite.code in _invite_cache[invite.guild.id]:
            del _invite_cache[invite.guild.id][invite.code]
        
        details = f"**Code:** {invite.code}\n**Channel:** {invite.channel.name}"
        
        await alert_info(bot, "Invite Deleted", details)
    
    except Exception as e:
        logger.exception(f'handle_invite_delete failed: {e}')
