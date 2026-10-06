<div align="center">

# ⚡ SAKIL AUTO ROTATOR PRO ⚡

[![PYTHON](https://img.shields.io/badge/PYTHON-3.10%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![TELEGRAM](https://img.shields.io/badge/TELEGRAM-BOT-blueviolet?style=flat-square&logo=telegram)](https://core.telegram.org/bots)
[![BOT STATUS](https://img.shields.io/badge/BOT-ACTIVE-success?style=flat-square)]()
[![DEVELOPER](https://img.shields.io/badge/DEVELOPER-SAKIL-critical?style=flat-square)](https://github.com/SakilSakil699)

An automated, ultra-fast & intelligent Telegram Channel Invite Link Rotator and Post Caption Updater.  
Designed for channel managers who need dynamic invite links, real-time caption sync, and powerful Sudo controls.

[💬 Contact Developer](https://t.me/your_username) • [📌 Features](#-key-features) • [🚀 Deploy Guide](#-repository-structure)

</div>

---

## 🌟 Key Features

- 🔄 **Automated Link Rotation:** Revokes expired invite links and issues fresh ones automatically at set intervals.
- ✏️ **Dynamic Caption Syncing:** Scans and updates all existing & new post captions with dynamic links in real-time.
- 🛡️ **Sudo Guard Architecture:** Advanced decorator protection to ensure only authorized admins can run control commands.
- 🔍 **Instant Auto-Discovery:** Automatically detects newly posted messages in channels without manual post ID entries.
- ⚡ **On-The-Fly Commands:** Change timing intervals, add sudos, or force-rotate directly via Telegram chat.
- 💾 **Intelligent JSON Caching:** Prevents API limit hits by caching cleaned message texts in `bot_data.json`.
- ⭐ **Embedded Developer Credits:** Every bot message and rotated caption includes stylish clickable credits pointing to the creator's profile.

---

## 📂 Repository Structure

```text
Sakil-Auto-Rotator-Pro/
├── 📄 main.py               # Core application logic & command handlers
├── ⚙️ config.py             # Environment configurations & credentials
├── 📦 requirements.txt      # Python dependency specifications
├── 🚀 Procfile              # Process launcher for Render / Heroku / Koyeb
├── 💾 bot_data.json         # Dynamic local cache & persistent database
└── 📖 README.md             # Documentation
