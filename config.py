import os

class Config:
    # 1. Telegram Bot Token (@BotFather se mila hua token yahan daalein)
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "6325577627:AAE9yJA_Egzq2-A0L25juz8JAM9gv2_TzxA")

    # 2. Log Channel ya Group ID (Yahan bot apna startup banner aur rotation logs bhejega, -100 se start hona chahiye)
    LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID", "-1001862025596")

    # 3. Rotation Interval (Seconds me, jaise 3600 seconds = 1 ghanta)
    ROTATE_INTERVAL = int(os.environ.get("ROTATE_INTERVAL", 60))

    # 4. Sudo Users List (Yahan apni Telegram User ID daalein taaki sirf aap commands access kar sakein)
    SUDO_USERS = [
        6024212623,  # Apni Telegram Numeric User ID yahan replace karein
    ]

    # 5. Multi-Channel Setup & Custom Branding Credits
    CHANNELS_DATA = {
        -1001987095581: {
            "credit_text": "Made by Sakil",
            "credit_link": "https://t.me/YO_UR_OFFICIAL_CRUSH",
            "post_ids": []  # Isse khali rehne dein, bot khud posts auto-detect kar lega
        },
        # Agar aur bhi channels add karne hon toh niche is tarah copy-paste kar sakte hain:
        # -100XXXXXXXXXX: {
        #     "credit_text": "Made by Sakil",
        #     "credit_link": "https://t.me/YO_UR_OFFICIAL_CRUSH",
        #     "post_ids": []
        # }
    }
