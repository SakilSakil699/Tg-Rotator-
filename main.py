import sys
import logging
import asyncio
import re
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
from config import Config

# Termux terminal me logs/status dikhane ke liye setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("SakilAutoRotator")

# Basic checks: Agar Token ya Channel Data missing hai toh script band ho jayegi
if not Config.BOT_TOKEN or not Config.CHANNELS_DATA:
    logger.error("BOT_TOKEN ya CHANNELS_DATA missing hai config.py me!")
    sys.exit(1)

LOG_CHAT_ID = int(Config.LOG_CHAT_ID) if Config.LOG_CHAT_ID else None
POST_CONTENTS = {}      # Post ke clean original text ko save karne ke liye
DYNAMIC_POST_IDS = {}   # Real-time me sabhi post IDs ko track karne ke liye

# Initial config se channel dictionary tayar karein
for ch_id, ids in Config.CHANNELS_DATA.items():
    DYNAMIC_POST_IDS[ch_id] = set(ids)


def clean_existing_links(content: str) -> str:
    """
    Purane Links, Duplicate Lines, aur Pehle Ke Credits ko Clean Karne Ka Function
    Isse text multiple times repeat nahi hoga.
    """
    if not content:
        return ""

    # 1. Purane HTML Hyperlink Tags remove karein
    content = re.sub(r'<a\s+href="[^"]*">.*?</a>', '', content, flags=re.IGNORECASE)
    
    # 2. Raw Telegram links remove karein
    content = re.sub(r'https://t\.me/(?:\+|\+[\w-]+|joinchat/[\w-]+|\w+)', '', content)
    
    # 3. Purane Click Here wale phrases remove karein
    content = re.sub(r'👉\s*Click\s+Here\s+To\s+Join\s+Channel', '', content, flags=re.IGNORECASE)
    content = re.sub(r'Click\s+Here\s+To\s+Join\s+Channel', '', content, flags=re.IGNORECASE)
    
    # 4. Purane Sakil Credits Clean karein
    content = re.sub(r'👤\s*Source/Owner:\s*Sakil', '', content, flags=re.IGNORECASE)
    content = re.sub(r'Made\s+by\s+Sakil', '', content, flags=re.IGNORECASE)

    # Clean lines format
    lines = [line.rstrip() for line in content.splitlines()]
    return "\n".join(lines).strip()


async def auto_discover_channel_posts(bot: Bot, channel_id: int):
    """
    Channel ki latest post ID auto-detect karke ID 1 se aakhri post tak list me shamil karta hai.
    Aapko manually post IDs dekhne ki zarurat nahi padegi.
    """
    try:
        # Ek dummy msg bhej kar latest Message ID pata karna aur instantly delete karna
        temp_msg = await bot.send_message(chat_id=channel_id, text="...")
        latest_id = temp_msg.message_id
        await bot.delete_message(chat_id=channel_id, message_id=latest_id)

        # 1 se lekar latest_id tak sabhi posts ko list me add kar lena
        all_ids = set(range(1, latest_id))
        DYNAMIC_POST_IDS[channel_id].update(all_ids)
        logger.info(f"Channel {channel_id} ki total {len(DYNAMIC_POST_IDS[channel_id])} posts auto-detect ho gayi!")

    except Exception as e:
        logger.warning(f"Auto-Discover failed for channel {channel_id}: {e}")


async def fetch_and_cache_post(bot: Bot, channel_id: int, msg_id: int):
    """
    Post ka original clean text memory me save karta hai.
    Agar beech me se koi post deleted ho (jaise 121 ya 125), toh bina crash hue skip ho jata hai.
    """
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
            # Deleted posts quiet skip hongi
            pass


async def update_channel_posts(bot: Bot, channel_id: int, new_link: str):
    """
    Posts ko update karke Bold Clickable Link aur Bold 'Made by Sakil' Watermark append karta hai.
    """
    # 1. Bold Rotated Hyperlink
    hyperlink_tag = f'<a href="{new_link}"><b>Click Here To Join Channel</b></a>'
    
    # 2. Bold Clickable Profile Credit (@YO_UR_OFFICIAL_CRUSH)
    sakil_credit = '<a href="https://t.me/YO_UR_OFFICIAL_CRUSH"><b>Made by Sakil</b></a>'

    active_post_ids = sorted(list(DYNAMIC_POST_IDS.get(channel_id, [])))

    for msg_id in active_post_ids:
        await fetch_and_cache_post(bot, channel_id, msg_id)
        
        cache_key = f"{channel_id}_{msg_id}"
        base_text = POST_CONTENTS.get(cache_key, "")

        if base_text:
            final_text = f"{base_text}\n\n👉 {hyperlink_tag}\n{sakil_credit}"
        else:
            final_text = f"👉 {hyperlink_tag}\n{sakil_credit}"

        edited = False
        
        # Files/APKs/Images Caption Edit
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

        # Text Messages Edit
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
    """
    Real-time Listener: Jaise hi aap channel me koi NAYI POST dalenge, 
    bot instantly us nayi post ki ID ko tracking list me add kar lega.
    """
    msg = update.channel_post
    if msg and msg.chat_id in DYNAMIC_POST_IDS:
        DYNAMIC_POST_IDS[msg.chat_id].add(msg.message_id)
        logger.info(f"Nayi post auto-detect hui Channel {msg.chat_id} me | Message ID: {msg.message_id}")


async def rotate_link_loop(app: Application):
    """
    Main background loop jo automatic link revoke aur new link create karke rotate karega.
    """
    bot = app.bot
    logger.info("Sakil's Multi-Channel Link Rotator Started Engine!")

    active_links = {}

    # Initial start par sabhi channels ki purani posts fetch karna
    for channel_id in Config.CHANNELS_DATA.keys():
        await auto_discover_channel_posts(bot, channel_id)

    while True:
        try:
            for channel_id in Config.CHANNELS_DATA.keys():
                # Purana link delete/revoke karna
                if channel_id in active_links:
                    try:
                        await bot.revoke_chat_invite_link(
                            chat_id=channel_id,
                            invite_link=active_links[channel_id]
                        )
                    except TelegramError:
                        pass

                # Naya link generate karna
                new_link_obj = await bot.create_chat_invite_link(
                    chat_id=channel_id,
                    name="Auto-Rotated Link"
                )
                new_link = new_link_obj.invite_link
                active_links[channel_id] = new_link

                # Update channel posts
                await update_channel_posts(bot, channel_id, new_link)

            # Admin log channel par message bhejna
            if LOG_CHAT_ID:
                await bot.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=f'🔄 All Channels & Posts Rotated Successfully!\nCredit: <a href="https://t.me/YO_UR_OFFICIAL_CRUSH"><b>Made by Sakil</b></a>',
                    parse_mode="HTML"
                )

        except Exception as e:
            logger.error(f"Execution Loop Error: {e}")

        # Sleep duration (Default 1 Ghanta)
        await asyncio.sleep(Config.ROTATE_INTERVAL)


def main():
    app = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Channel par listener lagayein
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post_handler))

    # Background task start karein
    asyncio.get_event_loop().create_task(rotate_link_loop(app))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
