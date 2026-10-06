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

# Environment Checks
if not Config.BOT_TOKEN:
    logger.error("BOT_TOKEN variable missing hai! Bot exit ho raha hai.")
    sys.exit(1)

if not Config.CHANNEL_ID:
    logger.error("CHANNEL_ID variable missing hai! Bot exit ho raha hai.")
    sys.exit(1)

try:
    CHANNEL_ID = int(Config.CHANNEL_ID)
except ValueError:
    logger.error("CHANNEL_ID ek valid integer number hona chahiye (e.g., -1001234567890).")
    sys.exit(1)

LOG_CHAT_ID = int(Config.LOG_CHAT_ID) if Config.LOG_CHAT_ID else None
current_invite_link = None


async def rotate_link_loop():
    global current_invite_link
    bot = Bot(token=Config.BOT_TOKEN)

    logger.info("Auto Link Rotator Engine Started Successfully!")

    while True:
        try:
            # Step 1: Purane Active Link ko Revoke / Deactivate karein
            if current_invite_link:
                try:
                    await bot.revoke_chat_invite_link(
                        chat_id=CHANNEL_ID,
                        invite_link=current_invite_link
                    )
                    logger.info(f"Purana Link Revoke Hua: {current_invite_link}")
                except TelegramError as e:
                    logger.warning(f"Purana link revoke nahi ho paya: {e}")

            # Step 2: Naya Fresh Invite Link Generate karein
            new_link_obj = await bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                name="Auto-Rotated Link"
            )
            current_invite_link = new_link_obj.invite_link
            logger.info(f"Naya Link Ban Gaya: {current_invite_link}")

            # Step 3: Naya link Admin / Log Chat par Bhejein (Agar configured ho)
            if LOG_CHAT_ID:
                msg_text = (
                    "🔄 **Telegram Channel Link Updated!**\n\n"
                    f"**Channel ID:** `{CHANNEL_ID}`\n"
                    f"**New Link:** {current_invite_link}\n\n"
                    f"⏱️ Next rotation in: `{Config.ROTATE_INTERVAL}` seconds."
                )
                await bot.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=msg_text,
                    parse_mode="Markdown"
                )

        except TelegramError as e:
            logger.error(f"Telegram API Exception: {e}")
        except Exception as e:
            logger.error(f"Unexpected Execution Error: {e}")

        # Agle rotation duration tak pause
        await asyncio.sleep(Config.ROTATE_INTERVAL)


if __name__ == "__main__":
    try:
        asyncio.run(rotate_link_loop())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot Stopped Successfully.")
