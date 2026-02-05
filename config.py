# config.py — Ultimate Configuration
import os

def _getenv_int(key):
    v = os.getenv(key)
    try:
        return int(v) if v is not None else None
    except ValueError:
        return None

def _getenv_bool(key, default='false'):
    return os.getenv(key, default).lower() in ('1', 'true', 'yes')

# ============= CORE SETTINGS =============
TOKEN = os.getenv('TOKEN') or None
OWNER_ID = _getenv_int('OWNER_ID')
GUILD_ID = _getenv_int('GUILD_ID')
PREFIX = '.'  # Fixed prefix for DM commands

# ============= BOT IDENTITY (STEALTH) =============
BOT_NAME = "Q"
BOT_STATUS = "🛠️ Server Helper"
BOT_ACTIVITY_TYPE = "watching"  # watching, playing, listening

# ============= NOTIFICATION SETTINGS =============
DM_ALERTS = _getenv_bool('DM_ALERTS', 'true')
# ALL ALERTS GO TO DM ONLY - NO SERVER CHANNELS!

# ============= MONITORING SETTINGS =============
# Default filters (can be changed via commands)
DEFAULT_FILTERS = {
    'roles': True,          # Role create/delete/update
    'channels': True,       # Channel create/delete/update
    'members': True,        # Member join/leave/update
    'messages': True,       # Message delete/edit (watched users only)
    'moderation': True,     # Ban/kick/timeout
    'server': True,         # Server settings/webhooks
    'bots': True,           # Bot additions (CRITICAL)
    'invites': True,        # Invite tracking
    'voice': True,          # Voice channel activity
}

# ============= PRIORITY LEVELS =============
PRIORITY_CRITICAL = ['bots', 'server', 'mass_delete']
PRIORITY_WARNING = ['roles', 'channels', 'moderation']
PRIORITY_INFO = ['members', 'voice', 'invites']

# ============= SECURITY =============
DB_ENCRYPTION_KEY = os.getenv('DB_KEY', 'default-key-change-me')  # Change this!
ENCRYPT_DB = _getenv_bool('ENCRYPT_DB', 'true')

# ============= RATE LIMITING =============
ALERT_COOLDOWN = 2  # seconds between alerts (anti-spam)
MAX_ALERTS_PER_MINUTE = 30  # Max alerts to owner per minute

# ============= QUICK ACTIONS =============
QUICK_ACTIONS_ENABLED = True
QUICK_ACTION_TIMEOUT = 300  # 5 minutes to respond

# ============= LOGGING =============
LOG_FILE = 'q_bot.log'
LOG_LEVEL = 'INFO'
LOG_TO_CONSOLE = True

# ============= FAKE COMMANDS (STEALTH) =============
ENABLE_FAKE_COMMANDS = True  # Public slash commands for cover
FAKE_COMMANDS_LIST = ['help', 'ping', 'serverinfo', 'avatar']

# Safety checks
if TOKEN is None:
    print('⚠️  WARNING: TOKEN not set in environment')
if OWNER_ID is None:
    print('⚠️  WARNING: OWNER_ID not set - DM commands will not work')
if GUILD_ID is None:
    print('⚠️  WARNING: GUILD_ID not set - bot will work in all servers')

print(f'✅ Config loaded: Bot={BOT_NAME}, Encryption={ENCRYPT_DB}, Guild={GUILD_ID}')
