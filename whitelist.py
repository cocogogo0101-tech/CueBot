# whitelist.py — Whitelist Management System
from db_manager import load_db, save_db, is_whitelisted
from logger import logger

def add_to_whitelist(user_id: int) -> tuple[bool, str]:
    """
    Add user to whitelist
    
    Returns:
        tuple: (success, message)
    """
    try:
        user_id_str = str(user_id)
        db = load_db()
        
        whitelist = db.get('whitelist', [])
        
        if user_id_str in whitelist:
            return False, f'❌ User `{user_id}` already in whitelist'
        
        whitelist.append(user_id_str)
        db['whitelist'] = whitelist
        save_db(db)
        
        logger.info(f'User {user_id} added to whitelist')
        return True, f'✅ User `{user_id}` added to whitelist'
    except Exception as e:
        logger.exception(f'Failed to add to whitelist: {e}')
        return False, f'❌ Error: {str(e)}'

def remove_from_whitelist(user_id: int) -> tuple[bool, str]:
    """
    Remove user from whitelist
    
    Returns:
        tuple: (success, message)
    """
    try:
        user_id_str = str(user_id)
        db = load_db()
        
        whitelist = db.get('whitelist', [])
        
        if user_id_str not in whitelist:
            return False, f'❌ User `{user_id}` not in whitelist'
        
        whitelist.remove(user_id_str)
        db['whitelist'] = whitelist
        save_db(db)
        
        logger.info(f'User {user_id} removed from whitelist')
        return True, f'✅ User `{user_id}` removed from whitelist'
    except Exception as e:
        logger.exception(f'Failed to remove from whitelist: {e}')
        return False, f'❌ Error: {str(e)}'

def get_whitelist_users() -> list:
    """Get list of whitelisted users"""
    db = load_db()
    return db.get('whitelist', [])

def get_whitelist_display() -> str:
    """Get formatted whitelist for display"""
    try:
        whitelist = get_whitelist_users()
        
        if not whitelist:
            return '📋 **Whitelist:** Empty'
        
        lines = ['📋 **Whitelisted Users:**\n']
        for i, user_id in enumerate(whitelist, 1):
            lines.append(f'{i}. `{user_id}`')
        
        return '\n'.join(lines)
    except Exception as e:
        logger.exception(f'Failed to get whitelist display: {e}')
        return f'❌ Error: {str(e)}'

def clear_whitelist() -> tuple[bool, str]:
    """Clear entire whitelist"""
    try:
        db = load_db()
        count = len(db.get('whitelist', []))
        db['whitelist'] = []
        save_db(db)
        
        logger.info('Whitelist cleared')
        return True, f'✅ Whitelist cleared ({count} users removed)'
    except Exception as e:
        logger.exception(f'Failed to clear whitelist: {e}')
        return False, f'❌ Error: {str(e)}'
