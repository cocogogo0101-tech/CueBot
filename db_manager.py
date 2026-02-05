# db_manager.py — Ultimate Database Manager with Encryption
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from logger import logger
from config import DB_ENCRYPTION_KEY, ENCRYPT_DB

DB_PATH = 'db.json'

# Generate encryption key from password
def _generate_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'q_bot_salt_2024',  # Static salt (في production استخدم salt عشوائي)
        iterations=100_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def _get_cipher():
    if not ENCRYPT_DB:
        return None
    key = _generate_key(DB_ENCRYPTION_KEY)
    return Fernet(key)

def load_db():
    """Load database from disk with optional decryption"""
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Decrypt if enabled
        if ENCRYPT_DB:
            try:
                cipher = _get_cipher()
                decrypted = cipher.decrypt(content.encode())
                data = json.loads(decrypted.decode())
                logger.debug('Database decrypted successfully')
                return data
            except Exception as e:
                logger.error(f'Decryption failed, trying plain JSON: {e}')
                # Fallback to plain JSON
                return json.loads(content)
        else:
            return json.loads(content)
            
    except FileNotFoundError:
        logger.info('Database not found, creating default')
        default = _get_default_db()
        save_db(default)
        return default
    except Exception as e:
        logger.exception(f'Failed to load database: {e}')
        return _get_default_db()

def save_db(data):
    """Save database to disk with optional encryption"""
    try:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        # Encrypt if enabled
        if ENCRYPT_DB:
            cipher = _get_cipher()
            encrypted = cipher.encrypt(json_str.encode())
            content = encrypted.decode()
        else:
            content = json_str
        
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug('Database saved successfully')
    except Exception as e:
        logger.exception(f'Failed to save database: {e}')

def _get_default_db():
    """Get default database structure"""
    return {
        "watched_users": [],
        "whitelist": [],
        "filters": {
            "roles": True,
            "channels": True,
            "members": True,
            "messages": True,
            "moderation": True,
            "server": True,
            "bots": True,
            "invites": True,
            "voice": True
        },
        "mask": {
            "channel_id": None,
            "reply_text": "━━━━━━━━━━━━"
        },
        "secret_channel_id": None,
        "quick_actions": {},
        "stats": {
            "total_alerts": 0,
            "bot_additions": 0,
            "role_changes": 0,
            "channel_changes": 0,
            "bans": 0,
            "kicks": 0
        },
        "audit_log": []
    }

def add_to_audit_log(event_type: str, details: dict):
    """Add event to audit log"""
    try:
        db = load_db()
        import datetime
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "type": event_type,
            "details": details
        }
        db['audit_log'].append(entry)
        
        # Keep only last 1000 entries
        if len(db['audit_log']) > 1000:
            db['audit_log'] = db['audit_log'][-1000:]
        
        save_db(db)
    except Exception as e:
        logger.exception(f'Failed to add audit log: {e}')

def increment_stat(stat_name: str):
    """Increment a statistic counter"""
    try:
        db = load_db()
        if stat_name in db['stats']:
            db['stats'][stat_name] += 1
        else:
            db['stats'][stat_name] = 1
        save_db(db)
    except Exception as e:
        logger.exception(f'Failed to increment stat: {e}')

def get_watched_users():
    """Get list of watched user IDs"""
    db = load_db()
    return db.get('watched_users', [])

def get_whitelist():
    """Get list of whitelisted user IDs"""
    db = load_db()
    return db.get('whitelist', [])

def is_watched(user_id: int) -> bool:
    """Check if user is being watched"""
    return str(user_id) in get_watched_users()

def is_whitelisted(user_id: int) -> bool:
    """Check if user is whitelisted"""
    return str(user_id) in get_whitelist()

def get_filter_status(filter_name: str) -> bool:
    """Get status of a specific filter"""
    db = load_db()
    return db.get('filters', {}).get(filter_name, True)

def get_all_filters():
    """Get all filter statuses"""
    db = load_db()
    return db.get('filters', {})