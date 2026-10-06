import os

class Config:
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    CHANNEL_ID = os.environ.get("CHANNEL_ID", "")
    LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID", "")
    ROTATE_INTERVAL = int(os.environ.get("ROTATE_INTERVAL", 86400))  # Default: 24 Hours
