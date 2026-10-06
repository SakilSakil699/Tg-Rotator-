import sys
import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from config import Config

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("LinkRotatorBot")

# Variable validation
if not Config.BOT_TOKEN or not Config.CHANNEL_ID:
    logger.error("BOT_TOKEN ya CHANNEL_ID missing hai!")
    sys.exit(1)

CHANNEL_ID = int(Config.CHANNEL_ID)
LOG_CHAT_ID = int(Config.LOG_CHAT_ID) if Config.LOG_CHAT_ID else None

# Environment variable se Post IDs extraction
POST_IDS_RAW = getattr(Config, 'POST_IDS', '')
POST_IDS = [int(i.strip()) for i in POST_IDS_RAW.split(",") if i.strip().isdigit()]

current_invite_link = None


async def update_channel_posts(bot: Bot, new_link: str):
    """Channel ki selected posts ka content update karein"""
    if not POST_IDS:
        logger.info("Koi POST_IDS set nahi hai, posts edit bypass ho rahi hain.")
        return

    for msg_id in POST_IDS:
        try:
            new_text = f"👉 **Join Our Channel:** {new_link}"
            
            await bot.edit_message_text(
                chat_id=CHANNEL_ID,
                message_id=msg_id,
                text=new_text,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            logger.info(f"Post ID {msg_id} ka link auto-update ho gaya!")
        except TelegramError as e:
            logger.warning(f"Post ID {msg_id} edit karne me issue aaya: {e}")


async def rotate_link_loop():
    global current_invite_link
    bot = Bot(token=Config.BOT_TOKEN)

    logger.info("Auto Link Rotator with Post Auto-Edit Started!")

    while True:
        try:
            # Step 1: Purana link revoke karein
            if current_invite_link:
                try:
                    await bot.revoke_chat_invite_link(
                        chat_id=CHANNEL_ID,
                        invite_link=current_invite_link
                    )
                    logger.info(f"Purana link revoke kar diya: {current_invite_link}")
                except TelegramError as e:
                    logger.warning(f"Purana link revoke nahi ho saka: {e}")

            # Step 2: Naya link create karein
            new_link_obj = await bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                name="Auto-Rotated Link"
            )
            current_invite_link = new_link_obj.invite_link
            logger.info(f"Naya Link Ban Gaya: {current_invite_link}")

            # Step 3: Targeted posts ka content/link change karein
            await update_channel_posts(bot, current_invite_link)

            # Step 4: Admin/Log notification
            if LOG_CHAT_ID:
                await bot.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=f"🔄 **Link Updated & Posts Edited!**\n\nNew Link: {current_invite_link}"
                )

        except TelegramError as e:
            logger.error(f"Telegram API Exception: {e}")
        except Exception as e:
            logger.error(f"Execution Exception: {e}")

        await asyncio.sleep(Config.ROTATE_INTERVAL)


if __name__ == "__main__":
    try:
        asyncio.run(rotate_link_loop())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot execution stopped.")
