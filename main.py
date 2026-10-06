import sys
import logging
import asyncio
import re
import json
import os
import subprocess
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.error import TelegramError, RetryAfter
from config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("SakilAutoRotatorPro")

DATA_FILE = "bot_data.json"

POST_CONTENTS = {}
DYNAMIC_POST_IDS = {}

# ==========================================
# ⚙️ YOUR DETAILS & CLICKABLE CREDITS
# ==========================================
DEVELOPER_NAME = getattr(Config, "DEVELOPER_NAME", "Sakil")
DEVELOPER_USERNAME = "YO_UR_OFFICIAL_CRUSH"  # Aapka Telegram Username
BOT_NAME = getattr(Config, "BOT_NAME", "Auto Rotator Pro Bot")

# Clickable Name Tag with Direct Telegram Profile Link
DEV_HYPERLINK = f'<a href="https://t.me/{DEVELOPER_USERNAME}"><b>{DEVELOPER_NAME}</b></a>'

# Premium Looking Footer Credit Strip
FOOTER_CREDIT = f"\n\n━━━━━━━━━━━━━━━━━━━━\n👑 <b>Developer:</b> {DEV_HYPERLINK}"


CURRENT_CONFIG = {
    "rotate_interval": Config.ROTATE_INTERVAL,
    "log_chat_id": Config.LOG_CHAT_ID,
    "channels_data": Config.CHANNELS_DATA,
    "sudo_users": getattr(Config, "SUDO_USERS", []),
    "developer_name": DEVELOPER_NAME,
    "developer_username": DEVELOPER_USERNAME,
    "bot_name": BOT_NAME
}


def load_data():
    global POST_CONTENTS, DYNAMIC_POST_IDS, CURRENT_CONFIG
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                POST_CONTENTS = data.get("post_contents", {})
                raw_ids = data.get("dynamic_post_ids", {})
                DYNAMIC_POST_IDS = {int(k): set(v) for k, v in raw_ids.items()}
                
                saved_cfg = data.get("config", {})
                if saved_cfg:
                    CURRENT_CONFIG["rotate_interval"] = saved_cfg.get("rotate_interval", Config.ROTATE_INTERVAL)
                    CURRENT_CONFIG["log_chat_id"] = saved_cfg.get("log_chat_id", Config.LOG_CHAT_ID)
                    CURRENT_CONFIG["sudo_users"] = saved_cfg.get("sudo_users", CURRENT_CONFIG["sudo_users"])
                    CURRENT_CONFIG["developer_name"] = saved_cfg.get("developer_name", CURRENT_CONFIG["developer_name"])
                    CURRENT_CONFIG["developer_username"] = saved_cfg.get("developer_username", CURRENT_CONFIG["developer_username"])
                    CURRENT_CONFIG["bot_name"] = saved_cfg.get("bot_name", CURRENT_CONFIG["bot_name"])
                    raw_ch = saved_cfg.get("channels_data", {})
                    if raw_ch:
                        CURRENT_CONFIG["channels_data"] = {int(k): v for k, v in raw_ch.items()}
                
                logger.info("Local JSON Cache & Config successfully loaded!")
        except Exception as e:
            logger.error(f"JSON Data load error: {e}")

    for ch_id, ch_info in CURRENT_CONFIG["channels_data"].items():
        if ch_id not in DYNAMIC_POST_IDS:
            DYNAMIC_POST_IDS[ch_id] = set(ch_info.get("post_ids", []))


def save_data():
    try:
        data = {
            "config": {
                "rotate_interval": CURRENT_CONFIG["rotate_interval"],
                "log_chat_id": CURRENT_CONFIG["log_chat_id"],
                "sudo_users": CURRENT_CONFIG["sudo_users"],
                "developer_name": CURRENT_CONFIG["developer_name"],
                "developer_username": CURRENT_CONFIG["developer_username"],
                "bot_name": CURRENT_CONFIG["bot_name"],
                "channels_data": {str(k): v for k, v in CURRENT_CONFIG["channels_data"].items()}
            },
            "post_contents": POST_CONTENTS,
            "dynamic_post_ids": {str(k): list(v) for k, v in DYNAMIC_POST_IDS.items()}
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Data save error: {e}")

load_data()


# Sudo Checking Decorator Guard
def sudo_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and user_id in CURRENT_CONFIG["sudo_users"]:
            return await func(update, context)
        else:
            if update.message:
                await update.message.reply_text(f"⛔ <b>Access Denied!</b> Tumhare paas Sudo permission nahi hai.{FOOTER_CREDIT}", parse_mode="HTML")
            return
    return wrapper


def clean_existing_links(content: str) -> str:
    if not content:
        return ""

    content = re.sub(r'<a\s+href="[^"]*">.*?</a>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'https://t\.me/(?:\+|\+[\w-]+|joinchat/[\w-]+|\w+)', '', content)
    content = re.sub(r'👉\s*Click\s+Here\s+To\s+Join\s+Channel', '', content, flags=re.IGNORECASE)
    content = re.sub(r'Click\s+Here\s+To\s+Join\s+Channel', '', content, flags=re.IGNORECASE)
    content = re.sub(r'👤\s*Source/Owner:\s*Sakil', '', content, flags=re.IGNORECASE)
    content = re.sub(r'Made\s+by\s+Sakil', '', content, flags=re.IGNORECASE)

    lines = [line.rstrip() for line in content.splitlines()]
    return "\n".join(lines).strip()


async def auto_discover_channel_posts(bot: Bot, channel_id: int):
    try:
        temp_msg = await bot.send_message(chat_id=channel_id, text="...")
        latest_id = temp_msg.message_id
        await bot.delete_message(chat_id=channel_id, message_id=latest_id)

        all_ids = set(range(1, latest_id))
        DYNAMIC_POST_IDS[channel_id].update(all_ids)
        save_data()
        logger.info(f"Channel {channel_id} ki total {len(DYNAMIC_POST_IDS[channel_id])} posts auto-detect ho gayi!")

    except Exception as e:
        logger.warning(f"Auto-Discover failed for channel {channel_id}: {e}")


async def fetch_and_cache_post(bot: Bot, channel_id: int, msg_id: int):
    cache_key = f"{channel_id}_{msg_id}"
    log_id = CURRENT_CONFIG["log_chat_id"]
    if cache_key not in POST_CONTENTS:
        try:
            target_log = int(log_id) if log_id else channel_id
            message = await bot.forward_message(
                chat_id=target_log,
                from_chat_id=channel_id,
                message_id=msg_id
            )
            if log_id:
                await bot.delete_message(chat_id=target_log, message_id=message.message_id)

            raw_content = message.caption or message.text or ""
            base_text = clean_existing_links(raw_content)
            POST_CONTENTS[cache_key] = base_text
            save_data()
        except TelegramError:
            pass


async def update_channel_posts(bot: Bot, channel_id: int, new_link: str):
    ch_config = CURRENT_CONFIG["channels_data"].get(channel_id, {})
    credit_txt = ch_config.get("credit_text", f"Made by {CURRENT_CONFIG['developer_name']}")
    credit_lnk = f"https://t.me/{CURRENT_CONFIG['developer_username']}"

    hyperlink_tag = f'<a href="{new_link}"><b>Click Here To Join Channel</b></a>'
    dev_credit = f'<a href="{credit_lnk}"><b>{credit_txt}</b></a>'

    active_post_ids = sorted(list(DYNAMIC_POST_IDS.get(channel_id, [])))

    for msg_id in active_post_ids:
        await fetch_and_cache_post(bot, channel_id, msg_id)
        
        cache_key = f"{channel_id}_{msg_id}"
        base_text = POST_CONTENTS.get(cache_key, "")

        if base_text:
            final_text = f"{base_text}\n\n👉 {hyperlink_tag}\n\n👤 {dev_credit}"
        else:
            final_text = f"👉 {hyperlink_tag}\n\n👤 {dev_credit}"

        edited = False
        try:
            await bot.edit_message_caption(
                chat_id=channel_id,
                message_id=msg_id,
                caption=final_text,
                parse_mode="HTML"
            )
            edited = True
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except TelegramError:
            pass

        if not edited:
            try:
                await bot.edit_message_text(
                    chat_id=channel_id,
                    message_id=msg_id,
                    text=final_text,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
            except TelegramError:
                pass

        await asyncio.sleep(0.5)


async def rotate_single_channel(bot: Bot, channel_id: int, active_links: dict):
    if channel_id in active_links:
        try:
            await bot.revoke_chat_invite_link(
                chat_id=channel_id,
                invite_link=active_links[channel_id]
            )
        except TelegramError:
            pass

    new_link_obj = await bot.create_chat_invite_link(
        chat_id=channel_id,
        name="Auto-Rotated Link"
    )
    new_link = new_link_obj.invite_link
    active_links[channel_id] = new_link

    await update_channel_posts(bot, channel_id, new_link)


async def perform_rotation(bot: Bot, active_links: dict):
    for channel_id in list(CURRENT_CONFIG["channels_data"].keys()):
        await rotate_single_channel(bot, channel_id, active_links)

    log_id = CURRENT_CONFIG["log_chat_id"]
    if log_id:
        try:
            await bot.send_message(
                chat_id=int(log_id),
                text=f'🔄 All Channels & Posts Rotated Successfully!\nCredit: {DEV_HYPERLINK}',
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed sending log message: {e}")


async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if msg and msg.chat_id in DYNAMIC_POST_IDS:
        DYNAMIC_POST_IDS[msg.chat_id].add(msg.message_id)
        save_data()
        logger.info(f"Nayi post auto-detect hui Channel {msg.chat_id} me | Message ID: {msg.message_id}")


# ==========================================
# 🌟 PUBLIC COMMANDS WITH HYPERLINK CREDITS
# ==========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name if update.effective_user else "User"
    bot_title = CURRENT_CONFIG["bot_name"]
    
    welcome_text = (
        f"👋 <b>Hello {user_name}!</b>\n\n"
        f"Welcome to <b>{bot_title}</b>!\n"
        f"Main aapke channels ki links aur posts ko auto-rotate karne wala pro bot hoon.\n\n"
        f"⚙️ <b>Available Commands:</b>\n"
        f"• /start - Restart / Start Bot\n"
        f"• /help - Bot Commands & Guide\n"
        f"• /about - Bot & Owner Information\n"
        f"• /ping - Check Bot Speed & Health\n\n"
        f"👤 <b>Main Controller:</b> {DEV_HYPERLINK}"
        f"{FOOTER_CREDIT}"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def help_command_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 <b>Bot Help & Guide</b>\n\n"
        "1. <b>Auto Rotation:</b> Bot har interval par configured channels ki links rotate karta hai.\n"
        "2. <b>Auto Post Update:</b> Channel ki sabhi purani aur nayi posts me fresh dynamic links auto-update ho jaati hain.\n"
        "3. <b>Sudo Access:</b> Commands control karne ke liye aapke paas Sudo access hona zaroori hai."
        f"{FOOTER_CREDIT}"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        f"ℹ️ <b>About {CURRENT_CONFIG['bot_name']}</b>\n\n"
        f"• <b>Version:</b> 2.0 Pro\n"
        f"• <b>Status:</b> Running Smoothly 24/7\n"
        f"• <b>Lead Developer:</b> {DEV_HYPERLINK}"
        f"{FOOTER_CREDIT}"
    )
    await update.message.reply_text(about_text, parse_mode="HTML", disable_web_page_preview=True)


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ping_text = (
        "🏓 <b>Pong!</b>\n"
        "Bot perfectly working halat me hai aur bilkul fast response de raha hai! ⚡"
        f"{FOOTER_CREDIT}"
    )
    await update.message.reply_text(ping_text, parse_mode="HTML")


# ==========================================
# 🛠️ SUDO COMMANDS WITH HYPERLINK CREDITS
# ==========================================

@sudo_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_ch = len(CURRENT_CONFIG["channels_data"])
    total_posts = sum(len(v) for v in DYNAMIC_POST_IDS.values())
    cached_texts = len(POST_CONTENTS)
    interval = CURRENT_CONFIG["rotate_interval"]
    log_ch = CURRENT_CONFIG["log_chat_id"]
    sudos = len(CURRENT_CONFIG["sudo_users"])

    msg = (
        f"<b>🤖 Sakil Rotator System Status</b>\n\n"
        f"<b>Rotation Interval:</b> {interval} sec ({round(interval/60, 1)} min)\n"
        f"<b>Log Channel ID:</b> <code>{log_ch}</code>\n"
        f"<b>Sudo Users Count:</b> {sudos}\n"
        f"<b>Target Channels:</b> {total_ch}\n"
        f"<b>Tracked Posts:</b> {total_posts}\n"
        f"<b>Cached Messages:</b> {cached_texts}\n"
        f"<b>Status:</b> Running 24/7 Smoothly 🚀"
        f"{FOOTER_CREDIT}"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


@sudo_only
async def add_sudo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(f"Usage: <code>/add_sudo &lt;user_id&gt;</code>{FOOTER_CREDIT}", parse_mode="HTML")
        return
    try:
        user_id = int(context.args[0].strip())
        if user_id not in CURRENT_CONFIG["sudo_users"]:
            CURRENT_CONFIG["sudo_users"].append(user_id)
            save_data()
            await update.message.reply_text(f"✅ User <code>{user_id}</code> added to Sudo list!{FOOTER_CREDIT}", parse_mode="HTML")
        else:
            await update.message.reply_text(f"⚠️ Ye user pehle se Sudo hai.{FOOTER_CREDIT}", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text(f"❌ Valid User ID daalo.{FOOTER_CREDIT}", parse_mode="HTML")


@sudo_only
async def remove_sudo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(f"Usage: <code>/remove_sudo &lt;user_id&gt;</code>{FOOTER_CREDIT}", parse_mode="HTML")
        return
    try:
        user_id = int(context.args[0].strip())
        if user_id in CURRENT_CONFIG["sudo_users"]:
            CURRENT_CONFIG["sudo_users"].remove(user_id)
            save_data()
            await update.message.reply_text(f"🗑️ User <code>{user_id}</code> removed from Sudo list!{FOOTER_CREDIT}", parse_mode="HTML")
        else:
            await update.message.reply_text(f"⚠️ Ye user Sudo list me nahi mila.{FOOTER_CREDIT}", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text(f"❌ Valid User ID daalo.{FOOTER_CREDIT}", parse_mode="HTML")


@sudo_only
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not CURRENT_CONFIG["channels_data"]:
        await update.message.reply_text(f"📁 Koi channel configured nahi hai.{FOOTER_CREDIT}", parse_mode="HTML")
        return

    text = "<b>📋 Configured Channels & Tracked Posts:</b>\n\n"
    for ch_id in CURRENT_CONFIG["channels_data"]:
        posts_count = len(DYNAMIC_POST_IDS.get(ch_id, []))
        text += f"• <b>Channel:</b> <code>{ch_id}</code> | <b>Posts:</b> {posts_count}\n"
    
    text += FOOTER_CREDIT
    await update.message.reply_text(text, parse_mode="HTML")


@sudo_only
async def force_rotate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ Force Rotation Initiated for ALL channels...", parse_mode="HTML")
    await perform_rotation(context.bot, getattr(context.app, "active_links", {}))
    await update.message.reply_text(f"✅ Force Rotation Completed!{FOOTER_CREDIT}", parse_mode="HTML")


@sudo_only
async def rotate_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(f"Usage: <code>/rotate_channel &lt;channel_id&gt;</code>{FOOTER_CREDIT}", parse_mode="HTML")
        return
    try:
        ch_id = int(context.args[0].strip())
        if ch_id in CURRENT_CONFIG["channels_data"]:
            await update.message.reply_text(f"⚡ Rotating single channel <code>{ch_id}</code>...", parse_mode="HTML")
            await rotate_single_channel(context.bot, ch_id, getattr(context.app, "active_links", {}))
            await update.message.reply_text(f"✅ Single channel <code>{ch_id}</code> rotated successfully!{FOOTER_CREDIT}", parse_mode="HTML")
        else:
            await update.message.reply_text(f"⚠️ Ye Channel config list me nahi hai.{FOOTER_CREDIT}", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text(f"❌ Valid Channel ID daalo.{FOOTER_CREDIT}", parse_mode="HTML")


@sudo_only
async def set_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(f"Usage: <code>/set_time &lt;seconds&gt;</code>\nExample: <code>/set_time 1800</code>{FOOTER_CREDIT}", parse_mode="HTML")
        return
    try:
        new_time = int(context.args[0])
        CURRENT_CONFIG["rotate_interval"] = new_time
        save_data()
        await update.message.reply_text(f"✅ Rotation interval set to <b>{new_time} seconds</b> ({round(new_time/60, 1)} mins)!{FOOTER_CREDIT}", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text(f"❌ Valid number daalo (seconds me).{FOOTER_CREDIT}", parse_mode="HTML")


@sudo_only
async def set_log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(f"Usage: <code>/set_log &lt;channel_id&gt;</code>{FOOTER_CREDIT}", parse_mode="HTML")
        return
    new_log = context.args[0].strip()
    CURRENT_CONFIG["log_chat_id"] = new_log
    save_data()
    await update.message.reply_text(f"✅ Log Channel ID set to <code>{new_log}</code>!{FOOTER_CREDIT}", parse_mode="HTML")


# ==========================================
# 🚀 MAIN RUNNER SETUP
# ==========================================

async def rotation_loop(app: Application):
    while True:
        try:
            await perform_rotation(app.bot, app.active_links)
        except Exception as e:
            logger.error(f"Rotation loop error: {e}")
        
        interval = CURRENT_CONFIG.get("rotate_interval", Config.ROTATE_INTERVAL)
        await asyncio.sleep(interval)


def main():
    token = getattr(Config, "BOT_TOKEN", None) or os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN config file me nahi mila!")
        sys.exit(1)

    app = Application.builder().token(token).build()
    app.active_links = {}

    # Public Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command_user))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("ping", ping_command))

    # Sudo Handlers
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("add_sudo", add_sudo_command))
    app.add_handler(CommandHandler("remove_sudo", remove_sudo_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("force_rotate", force_rotate_command))
    app.add_handler(CommandHandler("rotate_channel", rotate_channel_command))
    app.add_handler(CommandHandler("set_time", set_time_command))
    app.add_handler(CommandHandler("set_log", set_log_command))

    # Channel Handler
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post_handler))

    # Start Loop
    asyncio.get_event_loop().create_task(rotation_loop(app))

    logger.info("⚡ Sakil Auto Rotator Pro Bot Started Successfully!")
    app.run_polling()


if __name__ == "__main__":
    main()
