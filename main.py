import sys
import logging
import asyncio
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

current_invite_link = None


async def update_channel_posts(bot: Bot, new_link: str):
    """Channel ki Posts Text / Media Captions ko auto-edit karein"""
    if not POST_IDS:
        logger.info("POST_IDS configured nahi hai.")
        return

    for msg_id in POST_IDS:
        try:
            # Step A: Pehle Media Caption Edit karne ka try karein (Files/APKs ke liye)
            try:
                await bot.edit_message_caption(
                    chat_id=CHANNEL_ID,
                    message_id=msg_id,
                    caption=f"👉 **Join Our Channel:** {new_link}",
                    parse_mode="Markdown"
                )
                logger.info(f"Post ID {msg_id} (Media Caption) update ho gaya!")
                continue
            except TelegramError as e:
                # Agar Media nahi hai, toh standard message edit try karein
                if "There is no caption in the message to edit" in str(e) or "message is not modified" in str(e):
                    pass
                else:
                    logger.debug(f"Caption edit attempt info: {e}")

            # Step B: Normal Text Message Edit karein
            await bot.edit_message_text(
                chat_id=CHANNEL_ID,
                message_id=msg_id,
                text=f"👉 **Join Our Channel:** {new_link}",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            logger.info(f"Post ID {msg_id} (Text Message) update ho gaya!")

        except TelegramError as e:
            logger.warning(f"Post ID {msg_id} edit nahi ho paya: {e}")


async def rotate_link_loop():
    global current_invite_link
    bot = Bot(token=Config.BOT_TOKEN)

    logger.info("Auto Link Rotator with Caption Support Started!")

    while True:
        try:
            # 1. Purana link revoke karein
            if current_invite_link:
                try:
                    await bot.revoke_chat_invite_link(
                        chat_id=CHANNEL_ID,
                        invite_link=current_invite_link
                    )
                except TelegramError as e:
                    logger.warning(f"Purana link revoke issue: {e}")

            # 2. Naya Invite Link generate karein
            new_link_obj = await bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                name="Auto-Rotated Link"
            )
            current_invite_link = new_link_obj.invite_link
            logger.info(f"Naya Link Ban Gaya: {current_invite_link}")

            # 3. Channel posts & APK captions update karein
            await update_channel_posts(bot, current_invite_link)

            # 4. Admin/Logger Notification
            if LOG_CHAT_ID:
                await bot.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=f"🔄 **Link Updated & Posts Edited!**\n\nNaya Link: {current_invite_link}"
                )

        except Exception as e:
            logger.error(f"Execution Error: {e}")

        await asyncio.sleep(Config.ROTATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(rotate_link_loop())
