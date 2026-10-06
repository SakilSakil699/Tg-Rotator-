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
    """Channel ki posts me HTML format se Hyperlink text update karein"""
    if not POST_IDS:
        logger.info("Koi POST_IDS set nahi hai.")
        return

    # Hyperlink Text Format (HTML Mode)
    # Aap 'Click Here' ki jagah 'Touch Here' ya 'Join Channel' bhi likh sakte hain
    formatted_text = f'👉 <a href="{new_link}">Click Here To Join Channel</a>'

    for msg_id in POST_IDS:
        edited = False
        
        # 1. Media Caption Edit (Files/APKs ke liye)
        try:
            await bot.edit_message_caption(
                chat_id=CHANNEL_ID,
                message_id=msg_id,
                caption=formatted_text,
                parse_mode="HTML"
            )
            logger.info(f"Post ID {msg_id} (Caption Hyperlink) update ho gaya!")
            edited = True
        except TelegramError as e:
            logger.debug(f"Media Caption Edit Attempt for {msg_id}: {e}")

        # 2. Normal Text Message Edit (Agar Media na ho)
        if not edited:
            try:
                await bot.edit_message_text(
                    chat_id=CHANNEL_ID,
                    message_id=msg_id,
                    text=formatted_text,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                logger.info(f"Post ID {msg_id} (Text Hyperlink) update ho gaya!")
            except TelegramError as e:
                logger.warning(f"Post ID {msg_id} edit nahi ho paya: {e}")


async def rotate_link_loop():
    global current_invite_link
    bot = Bot(token=Config.BOT_TOKEN)

    logger.info("Auto Link Rotator with Hyperlink Started!")

    while True:
        try:
            # Step 1: Purana link revoke karein
            if current_invite_link:
                try:
                    await bot.revoke_chat_invite_link(
                        chat_id=CHANNEL_ID,
                        invite_link=current_invite_link
                    )
                except TelegramError as e:
                    logger.warning(f"Purana link revoke error: {e}")

            # Step 2: Naya link banayein
            new_link_obj = await bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                name="Auto-Rotated Link"
            )
            current_invite_link = new_link_obj.invite_link
            logger.info(f"Naya Link Ban Gaya: {current_invite_link}")

            # Step 3: Posts me Hyperlink update karein
            await update_channel_posts(bot, current_invite_link)

            # Step 4: Admin/Logger notification
            if LOG_CHAT_ID:
                await bot.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=f'🔄 Link Updated & Posts Edited!\n\nNaya Link: <a href="{current_invite_link}">Click Here</a>',
                    parse_mode="HTML"
                )

        except Exception as e:
            logger.error(f"Execution Error: {e}")

        await asyncio.sleep(Config.ROTATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(rotate_link_loop())
