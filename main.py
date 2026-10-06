import sys
import logging
import asyncio
import re
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
from config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("SakilAutoRotator")

if not Config.BOT_TOKEN or not Config.CHANNELS_DATA:
    logger.error("BOT_TOKEN ya CHANNELS_DATA missing hai config.py me!")
    sys.exit(1)

LOG_CHAT_ID = int(Config.LOG_CHAT_ID) if Config.LOG_CHAT_ID else None
POST_CONTENTS = {}
DYNAMIC_POST_IDS = {}

for ch_id, ids in Config.CHANNELS_DATA.items():
    DYNAMIC_POST_IDS[ch_id] = set(ids)


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
        logger.info(f"Channel {channel_id} ki total {len(DYNAMIC_POST_IDS[channel_id])} posts auto-detect ho gayi!")

    except Exception as e:
        logger.warning(f"Auto-Discover failed for channel {channel_id}: {e}")


async def fetch_and_cache_post(bot: Bot, channel_id: int, msg_id: int):
    cache_key = f"{channel_id}_{msg_id}"
    if cache_key not in POST_CONTENTS:
        try:
            message = await bot.forward_message(
                chat_id=LOG_CHAT_ID or channel_id,
                from_chat_id=channel_id,
                message_id=msg_id
            )
            if LOG_CHAT_ID:
                await bot.delete_message(chat_id=LOG_CHAT_ID, message_id=message.message_id)

            raw_content = message.caption or message.text or ""
            base_text = clean_existing_links(raw_content)
            POST_CONTENTS[cache_key] = base_text
        except TelegramError:
            pass


async def update_channel_posts(bot: Bot, channel_id: int, new_link: str):
    hyperlink_tag = f'<a href="{new_link}"><b>Click Here To Join Channel</b></a>'
    sakil_credit = '<a href="https://t.me/YO_UR_OFFICIAL_CRUSH"><b>Made by Sakil</b></a>'

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
            except TelegramError:
                pass


async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if msg and msg.chat_id in DYNAMIC_POST_IDS:
        DYNAMIC_POST_IDS[msg.chat_id].add(msg.message_id)
        logger.info(f"Nayi post auto-detect hui Channel {msg.chat_id} me | Message ID: {msg.message_id}")


async def rotate_link_loop(app: Application):
    bot = app.bot
    logger.info("Sakil's Multi-Channel Link Rotator Started Engine!")

    active_links = {}

    for channel_id in Config.CHANNELS_DATA.keys():
        await auto_discover_channel_posts(bot, channel_id)

    while True:
        try:
            for channel_id in Config.CHANNELS_DATA.keys():
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

            if LOG_CHAT_ID:
                await bot.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=f'🔄 All Channels & Posts Rotated Successfully!\nCredit: <a href="https://t.me/YO_UR_OFFICIAL_CRUSH"><b>Made by Sakil</b></a>',
                    parse_mode="HTML"
                )

        except Exception as e:
            logger.error(f"Execution Loop Error: {e}")

        await asyncio.sleep(Config.ROTATE_INTERVAL)


async def post_init(app: Application):
    asyncio.create_task(rotate_link_loop(app))


def main():
    app = Application.builder().token(Config.BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post_handler))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
