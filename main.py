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
CURRENT_CONFIG = {
    "rotate_interval": Config.ROTATE_INTERVAL,
    "log_chat_id": Config.LOG_CHAT_ID,
    "channels_data": Config.CHANNELS_DATA,
    "sudo_users": getattr(Config, "SUDO_USERS", [])
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


# Sudo Guard Decorator
def sudo_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and user_id in CURRENT_CONFIG["sudo_users"]:
            return await func(update, context)
        else:
            if update.message:
                await update.message.reply_text("⛔ **Access Denied!** Tumhare paas Sudo permission nahi hai.", parse_mode="Markdown")
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
    credit_txt = ch_config.get("credit_text", "Made by Sakil")
    credit_lnk = ch_config.get("credit_link", "https://t.me/YO_UR_OFFICIAL_CRUSH")

    hyperlink_tag = f'<a href="{new_link}"><b>Click Here To Join Channel</b></a>'
    sakil_credit = f'<a href="{credit_lnk}"><b>{credit_txt}</b></a>'

    active_post_ids = sorted(list(DYNAMIC_POST_IDS.get(channel_id, [])))

    for msg_id in active_post_ids:
        await fetch_and_cache_post(bot, channel_id, msg_id)
        
        cache_key = f"{channel_id}_{msg_id}"
        base_text = POST_CONTENTS.get(cache_key, "")

        if base_text:
            final_text = f"{base_text}\n\n👉 {hyperlink_tag}\n\n{sakil_credit}"
        else:
            final_text = f"👉 {hyperlink_tag}\n\n{sakil_credit}"

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
                text=f'🔄 <b>All Channels & Posts Rotated Successfully!</b>\n\n👑 <i>Developed & Managed by <b>Sakil</b></i>\n🔗 <a href="https://t.me/YO_UR_OFFICIAL_CRUSH"><b>Official Channel</b></a>',
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


# --- COMMANDS WITH SAKIL CREDIT MENU ---

@sudo_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"<b>🤖 Sakil's Pro Link Rotator Control Panel</b>\n\n"
        f"👑 <i>Created with ❤️️ by <b>Sakil</b></i>\n"
        f"🔗 <a href='https://t.me/YO_UR_OFFICIAL_CRUSH'><b>Support / Owner Profile</b></a>\n\n"
        f"<b>⚙️ Admin Commands List:</b>\n"
        f"• /status - Bot system health & stats\n"
        f"• /list - Tracked channels & posts list\n"
        f"• /force_rotate - Instant rotate all channels\n"
        f"• /rotate_channel <code>[id]</code> - Rotate single channel\n"
        f"• /set_time <code>[sec]</code> - Change rotation interval\n"
        f"• /set_log <code>[id]</code> - Update log group/channel ID\n"
        f"• /add_channel <code>[id]</code> - Add new channel\n"
        f"• /remove_channel <code>[id]</code> - Remove channel\n"
        f"• /add_post <code>[ch_id] [msg_id]</code> - Add specific post\n"
        f"• /remove_post <code>[ch_id] [msg_id]</code> - Remove specific post\n"
        f"• /add_sudo <code>[user_id]</code> - Add new admin\n"
        f"• /remove_sudo <code>[user_id]</code> - Remove admin\n"
        f"• /clear_cache - Clear text cache\n"
        f"• /git_pull - Update code from GitHub\n"
        f"• /restart - Restart bot via PM2\n"
    )
    await update.message.reply_text(help_text, parse_mode="HTML", disable_web_page_preview=True)


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
        f"👑 <b>Owner:</b> <a href='https://t.me/YO_UR_OFFICIAL_CRUSH'>Sakil</a>\n"
        f"<b>Rotation Interval:</b> {interval} sec ({round(interval/60, 1)} min)\n"
        f"<b>Log Channel ID:</b> <code>{log_ch}</code>\n"
        f"<b>Sudo Users Count:</b> {sudos}\n"
        f"<b>Target Channels:</b> {total_ch}\n"
        f"<b>Tracked Posts:</b> {total_posts}\n"
        f"<b>Cached Messages:</b> {cached_texts}\n"
        f"<b>Status:</b> Running 24/7 Smoothly 🚀"
    )
    await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)


@sudo_only
async def add_sudo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/add_sudo <user_id>`", parse_mode="Markdown")
        return
    try:
        user_id = int(context.args[0].strip())
        if user_id not in CURRENT_CONFIG["sudo_users"]:
            CURRENT_CONFIG["sudo_users"].append(user_id)
            save_data()
            await update.message.reply_text(f"✅ User `<code>{user_id}</code>` added to Sudo list!\n👑 <i>Managed by Sakil</i>", parse_mode="HTML")
        else:
            await update.message.reply_text("⚠️ Ye user pehle se Sudo hai.")
    except ValueError:
        await update.message.reply_text("❌ Valid User ID daalo.")


@sudo_only
async def remove_sudo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/remove_sudo <user_id>`", parse_mode="Markdown")
        return
    try:
        user_id = int(context.args[0].strip())
        if user_id in CURRENT_CONFIG["sudo_users"]:
            CURRENT_CONFIG["sudo_users"].remove(user_id)
            save_data()
            await update.message.reply_text(f"🗑️ User `<code>{user_id}</code>` removed from Sudo list!\n👑 <i>Managed by Sakil</i>", parse_mode="HTML")
        else:
            await update.message.reply_text("⚠️ Ye user Sudo list me nahi mila.")
    except ValueError:
        await update.message.reply_text("❌ Valid User ID daalo.")


@sudo_only
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not CURRENT_CONFIG["channels_data"]:
        await update.message.reply_text("📁 Koi channel configured nahi hai.")
        return

    text = "<b>📋 Configured Channels & Tracked Posts:</b>\n\n"
    for ch_id in CURRENT_CONFIG["channels_data"]:
        posts_count = len(DYNAMIC_POST_IDS.get(ch_id, []))
        text += f"• <b>Channel:</b> <code>{ch_id}</code> | <b>Posts:</b> {posts_count}\n"
    
    text += "\n👑 <i>Powered by Sakil Rotator Engine</i>"
    await update.message.reply_text(text, parse_mode="HTML")


@sudo_only
async def force_rotate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ Force Rotation Initiated for ALL channels...\n👑 <i>Managed by Sakil</i>", parse_mode="HTML")
    await perform_rotation(context.bot, getattr(context.app, "active_links", {}))
    await update.message.reply_text("✅ Force Rotation Completed!")


@sudo_only
async def rotate_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/rotate_channel <channel_id>`", parse_mode="Markdown")
        return
    try:
        ch_id = int(context.args[0].strip())
        if ch_id in CURRENT_CONFIG["channels_data"]:
            await update.message.reply_text(f"⚡ Rotating single channel `<code>{ch_id}</code>`...", parse_mode="HTML")
            await rotate_single_channel(context.bot, ch_id, getattr(context.app, "active_links", {}))
            await update.message.reply_text(f"✅ Single channel `<code>{ch_id}</code>` rotated successfully!\n👑 <i>By Sakil</i>", parse_mode="HTML")
        else:
            await update.message.reply_text("⚠️ Ye Channel config list me nahi hai.")
    except ValueError:
        await update.message.reply_text("❌ Valid Channel ID daalo.")


@sudo_only
async def set_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/set_time <seconds>`\nExample: `/set_time 1800` (for 30 mins)", parse_mode="Markdown")
        return
    try:
        new_time = int(context.args[0])
        CURRENT_CONFIG["rotate_interval"] = new_time
        save_data()
        await update.message.reply_text(f"✅ Rotation interval set to **{new_time} seconds** ({round(new_time/60, 1)} mins)!\n👑 *Managed by Sakil*", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Valid number daalo (seconds me).")


@sudo_only
async def set_log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/set_log <channel_id>`", parse_mode="Markdown")
        return
    new_log = context.args[0].strip()
    CURRENT_CONFIG["log_chat_id"] = new_log
    save_data()
    await update.message.reply_text(f"✅ Log Channel updated to: <code>{new_log}</code>\n👑 <i>By Sakil</i>", parse_mode="HTML")


@sudo_only
async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/add_channel <channel_id>`", parse_mode="Markdown")
        return
    try:
        ch_id = int(context.args[0].strip())
        if ch_id not in CURRENT_CONFIG["channels_data"]:
            CURRENT_CONFIG["channels_data"][ch_id] = {
                "credit_text": "Made by Sakil",
                "credit_link": "https://t.me/YO_UR_OFFICIAL_CRUSH",
                "post_ids": []
            }
            DYNAMIC_POST_IDS[ch_id] = set()
            save_data()
            await auto_discover_channel_posts(context.bot, ch_id)
            await update.message.reply_text(f"✅ Channel <code>{ch_id}</code> added & posts auto-detected!\n👑 <i>Engine by Sakil</i>", parse_mode="HTML")
        else:
            await update.message.reply_text("⚠️ Ye Channel pehle se added hai.")
    except ValueError:
        await update.message.reply_text("❌ Valid Channel ID daalo (-100 se start honi chahiye).")


@sudo_only
async def remove_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/remove_channel <channel_id>`", parse_mode="Markdown")
        return
    try:
        ch_id = int(context.args[0].strip())
        if ch_id in CURRENT_CONFIG["channels_data"]:
            del CURRENT_CONFIG["channels_data"][ch_id]
            if ch_id in DYNAMIC_POST_IDS:
                del DYNAMIC_POST_IDS[ch_id]
            save_data()
            await update.message.reply_text(f"🗑️ Channel <code>{ch_id}</code> removed!\n👑 <i>By Sakil</i>", parse_mode="HTML")
        else:
            await update.message.reply_text("⚠️ Ye Channel list me nahi mila.")
    except ValueError:
        await update.message.reply_text("❌ Valid Channel ID daalo.")


@sudo_only
async def add_post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/add_post <channel_id> <msg_id>`", parse_mode="Markdown")
        return
    try:
        ch_id = int(context.args[0].strip())
        msg_id = int(context.args[1].strip())
        if ch_id in DYNAMIC_POST_IDS:
            DYNAMIC_POST_IDS[ch_id].add(msg_id)
            save_data()
            await update.message.reply_text(f"✅ Post ID `{msg_id}` manually added for channel <code>{ch_id}</code>!\n👑 <i>By Sakil</i>", parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Pehle channel ko `/add_channel` se add karo.")
    except ValueError:
        await update.message.reply_text("❌ Valid numbers daalo.")


@sudo_only
async def remove_post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/remove_post <channel_id> <msg_id>`", parse_mode="Markdown")
        return
    try:
        ch_id = int(context.args[0].strip())
        msg_id = int(context.args[1].strip())
        if ch_id in DYNAMIC_POST_IDS and msg_id in DYNAMIC_POST_IDS[ch_id]:
            DYNAMIC_POST_IDS[ch_id].remove(msg_id)
            cache_key = f"{ch_id}_{msg_id}"
            POST_CONTENTS.pop(cache_key, None)
            save_data()
            await update.message.reply_text(f"🗑️ Post ID `{msg_id}` removed from channel <code>{ch_id}</code>!\n👑 <i>By Sakil</i>", parse_mode="HTML")
        else:
            await update.message.reply_text("⚠️️ Ye Post ID list me nahi mili.")
    except ValueError:
        await update.message.reply_text("❌ Valid numbers daalo.")


@sudo_only
async def clear_cache_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global POST_CONTENTS
    POST_CONTENTS.clear()
    save_data()
    await update.message.reply_text("🧹 Text cache cleared!\n👑 <i>Managed by Sakil</i>")


@sudo_only
async def git_pull_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Running `git pull origin main`...\n👑 *Sakil Rotator*", parse_mode="Markdown")
    try:
        result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, check=True)
        await update.message.reply_text(f"✅ **Git Pull Output:**\n```\n{result.stdout}\n```\n👑 *By Sakil*", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ **Git Pull Failed:**\n`{e}`", parse_mode="Markdown")


@sudo_only
async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻️ Restarting bot via PM2...\n👑 *Sakil Rotator Engine*", parse_mode="Markdown")
    try:
        subprocess.run(["pm2", "restart", "link-rotator"])
    except Exception as e:
        await update.message.reply_text(f"❌ Restart Error: `{e}`", parse_mode="Markdown")


async def rotate_link_loop(app: Application):
    bot = app.bot
    logger.info("Sakil's Pro Dynamic Rotator Engine Active!")

    # Startup pe Log Group ya Sudo owner ko Startup Banner bhejenge
    log_id = CURRENT_CONFIG["log_chat_id"]
    if log_id:
        try:
            startup_banner = (
                f"🚀 <b>Sakil's Pro Link Rotator Bot Started Successfully!</b>\n\n"
                f"👑 <b>Developed & Maintained by:</b> <a href='https://t.me/YO_UR_OFFICIAL_CRUSH'>Sakil</a>\n"
                f"⚡ <b>Engine Status:</b> Online & Running 24/7\n"
                f"📋 Type /help to view all admin commands.\n\n"
                f"<i>'Excellence in Automation by Sakil' ✨</i>"
            )
            await bot.send_message(chat_id=int(log_id), text=startup_banner, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"Failed to send startup banner: {e}")

    app.active_links = {}

    for channel_id in list(CURRENT_CONFIG["channels_data"].keys()):
        await auto_discover_channel_posts(bot, channel_id)

    while True:
        try:
            await perform_rotation(bot, app.active_links)
        except Exception as e:
            logger.error(f"Loop Error: {e}")

        await asyncio.sleep(CURRENT_CONFIG["rotate_interval"])


async def post_init(app: Application):
    asyncio.create_task(rotate_link_loop(app))


def main():
    app = Application.builder().token(Config.BOT_TOKEN).post_init(post_init).build()
    
    # Registering Commands with Sakil Credit Header
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("force_rotate", force_rotate_command))
    app.add_handler(CommandHandler("rotate_channel", rotate_channel_command))
    app.add_handler(CommandHandler("set_time", set_time_command))
    app.add_handler(CommandHandler("set_log", set_log_command))
    app.add_handler(CommandHandler("add_channel", add_channel_command))
    app.add_handler(CommandHandler("remove_channel", remove_channel_command))
    app.add_handler(CommandHandler("add_post", add_post_command))
    app.add_handler(CommandHandler("remove_post", remove_post_command))
    app.add_handler(CommandHandler("add_sudo", add_sudo_command))
    app.add_handler(CommandHandler("remove_sudo", remove_sudo_command))
    app.add_handler(CommandHandler("clear_cache", clear_cache_command))
    app.add_handler(CommandHandler("git_pull", git_pull_command))
    app.add_handler(CommandHandler("restart", restart_command))
    
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post_handler))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
