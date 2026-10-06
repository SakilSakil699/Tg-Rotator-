import sys
import logging
import asyncio
import re
from telegram import Bot
from telegram.error import TelegramError
from config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("LinkRotatorBot")

if not Config.BOT_TOKEN or not Config.CHANNEL_ID:
    logger.error("BOT_TOKEN ya CHANNEL_ID missing hai!")
    sys.exit(1)

CHANNEL_ID = int(Config.CHANNEL_ID)
LOG_CHAT_ID = int(Config.LOG_CHAT_ID) if Config.LOG_CHAT_ID else None

POST_IDS_RAW = getattr(Config, 'POST_IDS', '')
POST_IDS = [int(i.strip()) for i in POST_IDS_RAW.split(",") if i.strip().isdigit()]

# In-memory storage for post contents (No Manual JSON Needed)
POST_CONTENTS = {}
current_invite_link = None


async def fetch_and_cache_posts(bot: Bot):
    """Channel Posts se original content auto-fetch karein"""
    for msg_id in POST_IDS:
        if msg_id not in POST_CONTENTS:
            try:
                # Post ka object fetch karke message text/caption read karein
                message = await bot.forward_message(
                    chat_id=LOG_CHAT_ID or CHANNEL_ID,
                    from_chat_id=CHANNEL_ID,
                    message_id=msg_id
                )
                
                # Forwarded message message_id delete karein taaki log clean rahe
                if LOG_CHAT_ID:
                    await bot.delete_message(chat_id=LOG_CHAT_ID, message_id=message.message_id)

                content = message.caption or message.text or ""
                
                # Text me se purane invite links hata kar template marker ({LINK}) lagayein
                link_pattern = r'https://t\.me/(?:\+|\+[\w-]+|joinchat/[\w-]+)'
                
                if re.search(link_pattern, content):
                    cleaned_content = re.sub(link_pattern, "{LINK}", content)
                else:
                    cleaned_content = content + "\n\n👉 {LINK}"

                POST_CONTENTS[msg_id] = cleaned_content
                logger.info(f"Post ID {msg_id} ka original text auto-cache ho gaya!")

            except TelegramError as e:
                logger.warning(f"Post ID {msg_id} ka content read nahi ho saka: {e}")


async def update_channel_posts(bot: Bot, new_link: str):
    """Original Text Retain karke Hyperlink Rotate Karein"""
    if not POST_IDS:
        return

    # Pehle saari posts ka text auto-read karein
    await fetch_and_cache_posts(bot)

    hyperlink = f'<a href="{new_link}">Click Here To Join Channel</a>'

    for msg_id in POST_IDS:
        original_template = POST_CONTENTS.get(msg_id, "👉 {LINK}")
        final_text = original_template.replace("{LINK}", hyperlink)

        edited = False

        # 1. Media Caption Edit (Files/APKs ke liye)
        try:
            await bot.edit_message_caption(
                chat_id=CHANNEL_ID,
                message_id=msg_id,
                caption=final_text,
                parse_mode="HTML"
            )
            logger.info(f"Post ID {msg_id} (Caption) updated successfully!")
            edited = True
        except TelegramError as e:
            logger.debug(f"Media Caption Edit Attempt: {e}")

        # 2. Normal Text Message Edit
        if not edited:
            try:
                await bot.edit_message_text(
                    chat_id=CHANNEL_ID,
                    message_id=msg_id,
                    text=final_text,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                logger.info(f"Post ID {msg_id} (Text) updated successfully!")
            except TelegramError as e:
                logger.warning(f"Post ID {msg_id} edit failed: {e}")


async def rotate_link_loop():
    global current_invite_link
    bot = Bot(token=Config.BOT_TOKEN)

    logger.info("Fully Automatic Link Rotator Started!")

    while True:
        try:
            # Purana link revoke karein
            if current_invite_link:
                try:
                    await bot.revoke_chat_invite_link(
                        chat_id=CHANNEL_ID,
                        invite_link=current_invite_link
                    )
                except TelegramError:
                    pass

            # Naya link create karein
            new_link_obj = await bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                name="Auto-Rotated Link"
            )
            current_invite_link = new_link_obj.invite_link
            logger.info(f"Naya Link: {current_invite_link}")

            # Posts auto-update karein
            await update_channel_posts(bot, current_invite_link)

            # Admin Notification
            if LOG_CHAT_ID:
                await bot.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=f'🔄 Link Updated!\nNaya Link: <a href="{current_invite_link}">Click Here</a>',
                    parse_mode="HTML"
                )

        except Exception as e:
            logger.error(f"Execution Error: {e}")

        await asyncio.sleep(Config.ROTATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(rotate_link_loop())
