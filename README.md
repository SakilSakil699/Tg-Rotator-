# Tg-Rotator-
# Telegram Auto Channel Link Rotator Bot

Yeh Telegram Bot aapke channel ke invite link ko automatically periodic basis par rotate (change) karta rehta hai aur purane link ko cancel kar deta hai.

## Environment Variables

Hosting service par ye Variables set karein:

| Variable Name | Required | Description | Example |
|---|---|---|---|
| `BOT_TOKEN` | **Yes** | @BotFather se mila token | `123456789:ABCdefGhI...` |
| `CHANNEL_ID` | **Yes** | Telegram Channel ka ID | `-1001234567890` |
| `LOG_CHAT_ID` | No | Admin Chat/Channel ID updates ke liye | `987654321` ya `-100...` |
| `ROTATE_INTERVAL` | No | Seconds me link change interval (Default 86400 = 24 hr) | `3600` (1 Hour) |

## Quick Deployment Steps

1. Repostory Ko Fork / Push Karein GitHub Par.
2. [Render.com](https://render.com) par Login karein.
3. New **Background Worker** create karein aur GitHub repo connect karein.
4. Environment Variables fill karein.
5. Bot deploy aur run ho jayega!
