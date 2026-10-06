import os

class Config:
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    CHANNEL_ID = os.environ.get("CHANNEL_ID", "")
    LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID", "")
    ROTATE_INTERVAL = int(os.environ.get("ROTATE_INTERVAL", 86400))
    # Multiple post IDs comma-separated pass karein (e.g., "12,13,14")
    POST_IDS = os.environ.get("POST_IDS", "")
