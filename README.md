<div align="center">

  # ⚡ Telegram Multi-Channel Auto Link Rotator ⚡

  <p align="center">
    <b>A powerful, asynchronous, 24/7 automated Telegram invite link rotation engine with dynamic post discovery, watermark preservation, and multi-channel support.</b>
  </p>

  [![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Telegram API](https://img.shields.io/badge/Telegram-Bot%20API-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
  [![Process Manager](https://img.shields.io/badge/PM2-Daemon-green?style=for-the-badge&logo=pm2&logoColor=white)](https://pm2.keymetrics.io/)
  [![Maintained By](https://img.shields.io/badge/Made%20By-Sakil-ff69b4?style=for-the-badge)](https://t.me/YO_UR_OFFICIAL_CRUSH)

  <br />

  ---

</div>

## 📌 Features

- **🔄 Multi-Channel Support:** Manage and rotate links across multiple Telegram channels simultaneously using a unified configuration.
- **🔍 Auto-Discovery Engine:** Automatically scans and detects all existing post IDs (from ID 1 to latest) without manual entry.
- **⚡ Real-Time New Post Listener:** Tracks and automatically registers any newly uploaded channel posts on the fly.
- **🧼 Anti-Duplicate Clean Logic:** Smart Regex cleaning strips outdated invite links and formatting before applying fresh updates—no line duplication.
- **🛡️ Error & Deletion Resilience:** Automatically skips deleted post IDs (`MessageNotFound`) safely without stopping the background loop.
- **🎨 HTML Hyperlink Formatting:** Appends bold clickable join tags along with customized profile credits (`Made by Sakil`).
- **📱 24/7 Termux & PM2 Ready:** Ultra-lightweight and optimized for non-stop background execution via PM2 process manager.

---

## 🏗️ Project Architecture

```plain
Tg-Rotator-/
├── config.py          # Mapped Channel IDs, Token, and Rotation Settings
├── main.py            # Core Async Bot Logic, Event Listeners, & Regex Cleaner
├── requirements.txt    # Python Dependencies
└── README.md          # Project Documentation
