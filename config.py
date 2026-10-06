import os

class Config:
    # 1. Bot Token (@BotFather se mila hua main token)
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    
    # 2. Log Channel ya Aapki Personal Telegram ID (Notifications ke liye)
    LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID", "YOUR_LOG_CHANNEL_ID")
    
    # 3. Link Kitne Seconds Me Rotate Hoga (3600 Seconds = 1 Ghanta)
    ROTATE_INTERVAL = int(os.environ.get("ROTATE_INTERVAL", 3600))

    # 4. Multi-Channel Setup (Yahan khali brackets [] me IDs auto-detect hongi)
    # Bas -100... wali jagah apne Channels ki ID replace kar do:
    CHANNELS_DATA = {
        -1001847291039: [],  # Channel 1 ki ID
        -1000000000002: [],  # Channel 2 ki ID
        -1000000000003: []   # Channel 3 ki ID
    }
