# logger.py — Ultimate Logging System
import logging
import sys
from config import LOG_FILE, LOG_LEVEL, LOG_TO_CONSOLE

# Create logger
logger = logging.getLogger('q_bot')
logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

# Prevent duplicate handlers
if logger.hasHandlers():
    logger.handlers.clear()

# Format
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# File handler with rotation
try:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f'⚠️  Failed to create file handler: {e}')

# Console handler
if LOG_TO_CONSOLE:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Suppress discord.py verbose logging
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('discord.http').setLevel(logging.WARNING)
logging.getLogger('discord.gateway').setLevel(logging.WARNING)

logger.info('='*60)
logger.info('Q Bot Logger Initialized')
logger.info('='*60)
