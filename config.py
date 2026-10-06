import os

class Config:
    # ==========================================
    # 🔑 BOT AUTH & CREDENTIALS
    # ==========================================
    # BotFather se mila HTTP API Token yahan daalein
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

    # ==========================================
    # 👤 DEVELOPER & BRANDING DETAILS
    # ==========================================
    DEVELOPER_NAME = "Sakil"
    DEVELOPER_USERNAME = "YO_UR_OFFICIAL_CRUSH"  # Without @
    BOT_NAME = "Sakil Auto Rotator Pro"

    # ==========================================
    # 👑 SUDO / ADMIN USERS
    # ==========================================
    # Apni Telegram User ID yahan daalein (Rose bot me /id bhej kar check kar sakte hain)
    # Multiples users ke liye comma lagayein: [123456789, 987654321]
    SUDO_USERS = [
        int(x) for x in os.environ.get("SUDO_USERS", "123456789").split()
    ]

    # ==========================================
    # ⏱️ ROTATION SETTINGS
    # ==========================================
    # Auto Rotation interval (seconds me)
    # 1800 = 30 min | 3600 = 1 hour | 600 = 10 min
    ROTATE_INTERVAL = int(os.environ.get("ROTATE_INTERVAL", 1800))

    # ==========================================
    # 📊 LOG CHANNEL SETTINGS
    # ==========================================
    # Jahan rotation successful hone ke logs aayenge (Channel ID -100 se start hoti hai)
    LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID", "-1001234567890")

    # ==========================================
    # 📢 TARGET CHANNELS DATA
    # ==========================================
    # Jin channels me bot kaam karega (Channel ID daalna zaroori hai)
    # Baaki post_ids bot telegram se auto-detect kar lega
    CHANNELS_DATA = {
        -1001234567890: {
            "credit_text": "Made by Sakil",
            "credit_link": "https://t.me/YO_UR_OFFICIAL_CRUSH",
            "post_ids": []
        },
        # Dusra channel add karne ke liye niche uncomment (un-hash) karke format follow karein:
        # -1009876543210: {
        #     "credit_text": "Made by Sakil",
        #     "credit_link": "https://t.me/YO_UR_OFFICIAL_CRUSH",
        #     "post_ids": []
        # },
    }
