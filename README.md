<div align="center">

# 🤖 Sakil's Pro Telegram Multi-Channel Link Rotator

> **An advanced, automated 24/7 Telegram link rotation engine built for Termux & Cloud servers, featuring dynamic post auto-discovery, persistent JSON caching, per-channel branding, anti-spam delay limits, and full remote control via Sudo commands.**

👑 **Developed & Maintained by [Sakil](https://t.me/YO_UR_OFFICIAL_CRUSH)**

</div>

---

## 🌟 Advanced Features

* **🔄 24/7 Automated Link Rotation:** Automatically revokes old chat invite links and generates fresh links at custom intervals.
* **⚡ Dynamic Post Auto-Discovery:** Automatically scans and detects all past posts in your channels without manual IDs configuration.
* **💾 Persistent JSON Storage:** Safely caches post contents and IDs in `bot_data.json` to prevent data loss on unexpected reboots.
* **🛡️ Sudo Security Guard:** Restricts all sensitive admin controls (`/restart`, `/git_pull`, `/set_time`, etc.) strictly to authorized owner IDs.
* **⏱️ Anti-Spam Rate Limit Shield:** Implements intelligent `RetryAfter` exception handling and safe delays to prevent Telegram flood blocks.
* **🎨 Custom Branding & Spacing:** Cleans old links and cleanly appends your custom hyperlinked call-to-action credit on a separate line.
* **📱 Remote Control Panel:** Manage everything directly from Telegram using advanced slash commands.

---

## 📋 Complete Admin Commands List

| Command | Description |
| :--- | :--- |
| `/help` | View the interactive control panel menu with full credits. |
| `/status` | Check system health, active interval, and tracking stats. |
| `/list` | List all connected target channels and their post counts. |
| `/force_rotate` | Trigger an immediate rotation across all channels instantly. |
| `/rotate_channel <id>` | Rotate the invite link for one specific channel. |
| `/set_time <sec>` | Change the automatic rotation interval duration in seconds. |
| `/set_log <id>` | Update the log group/channel destination ID. |
| `/add_channel <id>` | Add a new target channel and auto-discover its posts. |
| `/remove_channel <id>` | Remove a channel from active tracking. |
| `/add_post <ch_id> <msg_id>` | Manually include a specific post ID. |
| `/remove_post <ch_id> <msg_id>` | Manually remove a specific post ID from tracking. |
| `/add_sudo <user_id>` | Authorize a new admin/sudo user. |
| `/remove_sudo <user_id>` | Revoke admin access from a user. |
| `/clear_cache` | Clear stored text cache to refresh post contents. |
| `/git_pull` | Pull the latest updates directly from your GitHub repository. |
| `/restart` | Restart the bot process gracefully via PM2. |

---

## ⚙️ Configuration Setup (`config.py`)

Create or update your `config.py` file with the following structure:

```python
import os

class Config:
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID", "-1001862025596")
    ROTATE_INTERVAL = int(os.environ.get("ROTATE_INTERVAL", 3600))
    
    # Your Telegram Numeric User ID for command security
    SUDO_USERS = [123456789] 

    CHANNELS_DATA = {
        -1001987095581: {
            "credit_text": "Made by Sakil",
            "credit_link": "[https://t.me/YO_UR_OFFICIAL_CRUSH](https://t.me/YO_UR_OFFICIAL_CRUSH)",
            "post_ids": []
        }
    }
🚀 Installation & Deployment (Termux / Linux)
Clone or Update Repository:
git clone [https://github.com/SakilSakil699/Tg-Rotator.git](https://github.com/SakilSakil699/Tg-Rotator.git)
cd Tg-Rotator
