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

POST_CONTENTS = {}
current_invite_link = None


def clean_existing_links(content: str) -> str:
    """Purane Hyperlink Tags, Text, aur Links ko completely clean karein"""
    if not content:
        return ""

    # 1. HTML A-Tags (Hyperlinks) remove karein
    content = re.sub(r'<a\s+href="[^"]*">.*?</a>', '', content, flags=re.IGNORECASE)
    
    # 2. Open Telegram URLs remove karein
    content = re.sub(r'https://t\.me/(?:\+|\+[\w-]+|joinchat/[\w-]+|\w+)', '', content)

    # 3. Repeat hone wale "👉 Click Here To Join Channel" phrases/lines remove karein
    content = re.sub(r'👉\s*Click\s+Here\s+To\s+Join\s+Channel', '', content, flags=re.IGNORECASE)
    content = re.sub(r'Click\s+Here\s+To\s+Join\s+Channel', '', content, flags=re.IGNORECASE)

    # Clean multiple trailing newlines
    lines = [line.rstrip() for line in content.splitlines()]
    cleaned_text = "\n".join(lines).strip()
    
    return cleaned_text


async def fetch_and_cache_posts(bot: Bot):
    """Channel Posts se Clean Original Content Auto-Fetch Karein"""
    for msg_id in POST_IDS:
        if msg_id not in POST_CONTENTS:
            try:
                message = await bot.forward_message(
                    chat_id=LOG_CHAT_ID or CHANNEL_ID,
                    from_chat_id=CHANNEL_ID,
                    message_id=msg_id
                )
                
                if LOG_CHAT_ID:
                    await bot.delete_message(chat_id=LOG_CHAT_ID, message_id=message.message_id)

                raw_content = message.caption or message.text or ""
                
                # Purana har tarah ka link text strip karke base template rakhein
                base_text = clean_existing_links(raw_content)
                POST_CONTENTS[msg_id] = base_text
                logger.info(f"Post ID {msg_id} ka clean base text auto-cache ho gaya!")

            except TelegramError as e:
                logger.warning(f"Post ID {msg_id} fetch error: {e}")


async def update_channel_posts(bot: Bot, new_link: str):
    """Clean Base Text me Exactly EK Rotated Hyperlink Append Karein"""
    if not POST_IDS:
        return

    await fetch_and_cache_posts(bot)

    hyperlink_tag = f'<a href="{new_link}">Click Here To Join Channel</a>'

    for msg_id in POST_IDS:
        base_text = POST_CONTENTS.get(msg_id, "")
        
        # Single clean line format
        if base_text:
            final_text = f"{base_text}\n\n👉 {hyperlink_tag}"
        else:
            final_text = f"👉 {hyperlink_tag}"

        edited = False

        # 1. Media Caption Edit (Files/APKs)
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

        # 2. Text Message Edit
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

    logger.info("Duplicates-Free Auto Link Rotator Started!")

    while True:
        try:
            if current_invite_link:
                try:
                    await bot.revoke_chat_invite_link(
                        chat_id=CHANNEL_ID,
                        invite_link=current_invite_link
                    )
                except TelegramError:
                    pass

            new_link_obj = await bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                name="Auto-Rotated Link"
            )
            current_invite_link = new_link_obj.invite_link
            logger.info(f"Naya Link: {current_invite_link}")

            await update_channel_posts(bot, current_invite_link)

            if LOG_CHAT_ID:
                await bot.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=f'🔄 Link Rotated!\nNaya Link: <a href="{current_invite_link}">Click Here</a>',
                    parse_mode="HTML"
                )

        except Exception as e:
            logger.error(f"Execution Error: {e}")

        await asyncio.sleep(Config.ROTATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(rotate_link_loop())
