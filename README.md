<div align="center">

# ⚡ SAKIL AUTO ROTATOR PRO ⚡

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![Telegram API](https://img.shields.io/badge/Telegram-python--telegram--bot-2CA5E0.svg?style=for-the-badge&logo=telegram)](https://python-telegram-bot.org/)
[![Status](https://img.shields.io/badge/Bot_Status-Active_24%2F7-brightgreen.svg?style=for-the-badge)](https://t.me/YO_UR_OFFICIAL_CRUSH)
[![Developer](https://img.shields.io/badge/Developer-Sakil-ff69b4.svg?style=for-the-badge&logo=telegram)](https://t.me/YO_UR_OFFICIAL_CRUSH)

<p align="center">
  <b>An automated, ultra-fast & intelligent Telegram Channel Invite Link Rotator and Post Caption Updater.</b>
  <br />
  Designed for channel managers who need dynamic invite links, real-time caption sync, and powerful Sudo controls.
</p>

---

[👑 Contact Developer](https://t.me/YO_UR_OFFICIAL_CRUSH) • [📖 Features](#-key-features) • [🚀 Deploy Guide](#-quick-deployment)

</div>

---

<a name="-key-features"></a>
## 🌟 Key Features

* **🔄 Automated Link Rotation:** Revokes expired invite links and issues fresh ones automatically at set intervals.
* **📝 Dynamic Caption Syncing:** Scans and updates all existing & new post captions with dynamic links in real-time.
* **🛡️ Sudo Guard Architecture:** Advanced decorator protection to ensure only authorized admins can run control commands.
* **🔍 Instant Auto-Discovery:** Automatically detects newly posted messages in channels without manual post ID entries.
* **⚡ On-The-Fly Commands:** Change timing intervals, add sudos, or force-rotate directly via Telegram chat.
* **💾 Intelligent JSON Caching:** Prevents API limit hits by caching cleaned message texts in `bot_data.json`.
* **👑 Embedded Developer Credits:** Every bot message and rotated caption includes stylish clickable credits pointing to the creator's profile.

---

## 📁 Repository Structure

```text
📂 Sakil-Auto-Rotator-Pro
 ├── 📜 main.py              # Core application logic & command handlers
 ├── ⚙️ config.py            # Environment configurations & credentials
 ├── 📦 requirements.txt     # Python dependency specifications
 ├── 🚀 Procfile             # Process launcher for Render / Heroku / Koyeb
 ├── 💾 bot_data.json        # Dynamic local cache & persistent database
 └── 📄 README.md            # Documentation
