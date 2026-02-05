# filters.py — Ultimate Notification Filter System
from db_manager import load_db, save_db, get_filter_status, is_whitelisted
from logger import logger
from config import PRIORITY_CRITICAL, PRIORITY_WARNING, PRIORITY_INFO

def should_alert(event_type: str, user_id: int = None) -> bool:
    """
    Determine if an alert should be sent based on filters and whitelist
    
    Args:
        event_type: Type of event (roles, channels, members, etc.)
        user_id: User ID involved (if applicable)
    
    Returns:
        bool: True if alert should be sent
    """
    # Always alert for critical events
    if event_type in PRIORITY_CRITICAL:
        return True
    
    # Check if user is whitelisted (skip non-critical alerts)
    if user_id and is_whitelisted(user_id):
        logger.debug(f'User {user_id} is whitelisted, skipping alert for {event_type}')
        return False
    
    # Check filter status
    filter_enabled = get_filter_status(event_type)
    
    if not filter_enabled:
        logger.debug(f'Filter {event_type} is disabled, skipping alert')
        return False
    
    return True

def get_priority(event_type: str) -> str:
    """Get priority level for event type"""
    if event_type in PRIORITY_CRITICAL:
        return '🔴 CRITICAL'
    elif event_type in PRIORITY_WARNING:
        return '🟡 WARNING'
    elif event_type in PRIORITY_INFO:
        return '🟢 INFO'
    else:
        return '⚪ UNKNOWN'

def toggle_filter(filter_name: str) -> tuple[bool, str]:
    """
    Toggle a filter on/off
    
    Returns:
        tuple: (success, new_status_text)
    """
    try:
        db = load_db()
        filters = db.get('filters', {})
        
        if filter_name not in filters:
            return False, f'❌ Filter `{filter_name}` not found'
        
        # Toggle
        filters[filter_name] = not filters[filter_name]
        db['filters'] = filters
        save_db(db)
        
        status = 'تشغيل ✅' if filters[filter_name] else 'إيقاف ❌'
        logger.info(f'Filter {filter_name} toggled to {filters[filter_name]}')
        
        return True, f'✅ Filter `{filter_name}` → {status}'
    except Exception as e:
        logger.exception(f'Failed to toggle filter: {e}')
        return False, f'❌ Error: {str(e)}'

def set_filter(filter_name: str, enabled: bool) -> tuple[bool, str]:
    """
    Set a filter to specific state
    
    Returns:
        tuple: (success, message)
    """
    try:
        db = load_db()
        filters = db.get('filters', {})
        
        if filter_name not in filters:
            return False, f'❌ Filter `{filter_name}` not found'
        
        filters[filter_name] = enabled
        db['filters'] = filters
        save_db(db)
        
        status = 'تشغيل ✅' if enabled else 'إيقاف ❌'
        logger.info(f'Filter {filter_name} set to {enabled}')
        
        return True, f'✅ Filter `{filter_name}` → {status}'
    except Exception as e:
        logger.exception(f'Failed to set filter: {e}')
        return False, f'❌ Error: {str(e)}'

def get_filters_status() -> str:
    """Get formatted string of all filters"""
    try:
        db = load_db()
        filters = db.get('filters', {})
        
        lines = ['📋 **Filters Status:**\n']
        
        for category, priority_list in [
            ('🔴 Critical', PRIORITY_CRITICAL),
            ('🟡 Warning', PRIORITY_WARNING),
            ('🟢 Info', PRIORITY_INFO)
        ]:
            lines.append(f'\n**{category}:**')
            for f in filters:
                if f in priority_list:
                    status = '✅' if filters[f] else '❌'
                    lines.append(f'  • `{f}`: {status}')
        
        # Rest of filters
        other_filters = [f for f in filters if f not in PRIORITY_CRITICAL + PRIORITY_WARNING + PRIORITY_INFO]
        if other_filters:
            lines.append('\n**⚪ Other:**')
            for f in other_filters:
                status = '✅' if filters[f] else '❌'
                lines.append(f'  • `{f}`: {status}')
        
        return '\n'.join(lines)
    except Exception as e:
        logger.exception(f'Failed to get filters status: {e}')
        return f'❌ Error: {str(e)}'

def enable_all_filters() -> str:
    """Enable all filters"""
    try:
        db = load_db()
        filters = db.get('filters', {})
        for key in filters:
            filters[key] = True
        db['filters'] = filters
        save_db(db)
        logger.info('All filters enabled')
        return '✅ تم تشغيل جميع الفلاتر'
    except Exception as e:
        logger.exception(f'Failed to enable all filters: {e}')
        return f'❌ Error: {str(e)}'

def disable_all_filters() -> str:
    """Disable all filters (except critical)"""
    try:
        db = load_db()
        filters = db.get('filters', {})
        for key in filters:
            # Keep critical filters enabled
            if key not in PRIORITY_CRITICAL:
                filters[key] = False
        db['filters'] = filters
        save_db(db)
        logger.info('All non-critical filters disabled')
        return '✅ تم إيقاف جميع الفلاتر (ما عدا الحرجة)'
    except Exception as e:
        logger.exception(f'Failed to disable filters: {e}')
        return f'❌ Error: {str(e)}'

def reset_filters() -> str:
    """Reset filters to default"""
    try:
        from config import DEFAULT_FILTERS
        db = load_db()
        db['filters'] = DEFAULT_FILTERS.copy()
        save_db(db)
        logger.info('Filters reset to default')
        return '✅ تم إعادة ضبط الفلاتر للإعدادات الافتراضية'
    except Exception as e:
        logger.exception(f'Failed to reset filters: {e}')
        return f'❌ Error: {str(e)}'
