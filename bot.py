import os
import sys
import logging
import threading
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import database

# Quick Reply Templates for Admin
QUICK_REPLIES = {
    "1": "🙏 ទទួលបានហើយ! សូមរង់ចាំបន្តិច Team នឹងឆ្លើយតបជូនបងអូនឆាប់ៗនេះ",
    "2": "Done send  ✅ Please check your inbox and accept to get premium",
    "3": "Done Activated ✅ Please take a moment to review it.",
    "4": "Please use the Gmail ✅ account we provided to request your login code from us.",
    "5": "Once it’s completed, we will inform you 🥰 Our team is processing your order now",
    "6": "we not available for now 🥰 Please follow our groups to get new",
    "7": "Thank you Dear, for reaching out to us! We’re here to support you with any issues you may encounter.🥰🙏",
    "8": "We have received bong Please allow us 10-15 minutes to activate your account. Thank you! 🫰",
    "9": "Please send us your Gmail address, and our team will check it for you soon 🥰",
    "10": "Any problems? ⚠️ Please send us a screenshot or details to make it easier for us to help you. 🥰",
    "11": "Your plan has expired 🥰",
}

def get_quick_reply_keyboard(customer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1️⃣ រង់ចាំបន្តិច", callback_data=f"qr:{customer_id}:1"),
            InlineKeyboardButton("2️⃣ Done Send", callback_data=f"qr:{customer_id}:2"),
        ],
        [
            InlineKeyboardButton("3️⃣ Done Activated", callback_data=f"qr:{customer_id}:3"),
            InlineKeyboardButton("4️⃣ Gmail Code", callback_data=f"qr:{customer_id}:4"),
        ],
        [
            InlineKeyboardButton("5️⃣ Processing", callback_data=f"qr:{customer_id}:5"),
            InlineKeyboardButton("6️⃣ Not Available", callback_data=f"qr:{customer_id}:6"),
        ],
        [
            InlineKeyboardButton("7️⃣ Thank You", callback_data=f"qr:{customer_id}:7"),
            InlineKeyboardButton("8️⃣ 10-15 Mins", callback_data=f"qr:{customer_id}:8"),
        ],
        [
            InlineKeyboardButton("9️⃣ Send Gmail", callback_data=f"qr:{customer_id}:9"),
            InlineKeyboardButton("🔟 Screenshot", callback_data=f"qr:{customer_id}:10"),
        ],
        [
            InlineKeyboardButton("1️⃣1️⃣ Plan Expired", callback_data=f"qr:{customer_id}:11"),
        ],
    ])

# Directory for welcome/auto-reply images
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image")

def get_latest_image_path():
    if not os.path.exists(IMAGE_DIR):
        return None
    valid_exts = ('.png', '.jpg', '.jpeg', '.webp')
    images = [
        os.path.join(IMAGE_DIR, f)
        for f in os.listdir(IMAGE_DIR)
        if f.lower().endswith(valid_exts)
    ]
    if not images:
        return None
    images.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return images[0]

async def send_welcome_or_autoreply(update: Update, text: str):
    image_path = get_latest_image_path()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 ចូលមើល Website", url="https://proservicepremium.site.je")]
    ])

    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=keyboard
                )
                return
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")

    # Fallback to plain text if photo sending fails or no photo
    await update.message.reply_text(
        text=text,
        reply_markup=keyboard
    )

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or "9076272219:AAEkIbp1KKlVRBqmsuOB_S1Vcc33hYZVH1s"
ADMIN_ID_RAW = os.getenv("ADMIN_ID") or "7451912153"
ADMIN_IDS = [int(x.strip()) for x in ADMIN_ID_RAW.split(",") if x.strip().isdigit()]

COOLDOWN_MINUTES = int(os.getenv("AUTO_REPLY_COOLDOWN_MINUTES", "1440"))  # 24 hours = 1440 minutes

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    if is_admin(user.id):
        help_text = (
            "👑 <b>ផ្ទាំងគ្រប់គ្រង Admin (Admin Dashboard)</b>\n\n"
            "Bot កំពុងដំណើរការជាធម្មតា!\n\n"
            "📌 <b>របៀបឆ្លើយតបទៅកាន់ភ្ញៀវ៖</b>\n"
            "• ពេលមានភ្ញៀវឆាតមក Bot នឹងបញ្ជូនសារមកទីនេះ។\n"
            "• លោកអ្នកគ្រាន់តែចុច <b>Reply</b> លើសារនោះ រួចវាយសារតបវិញ នោះ Bot នឹងផ្ញើជូនភ្ញៀវភ្លាមៗ។\n\n"
            "🛠 <b>បញ្ជាផ្សេងៗ (Commands):</b>\n"
            "• /templates - មើលបញ្ជី Quick Reply Templates ទាំង ១១\n"
            "• /users - មើលចំនួនភ្ញៀវសរុប និង ៥ នាក់ចុងក្រោយ\n"
            "• /reply &lt;ID&gt; &lt;សារ&gt; - ផ្ញើសារទៅកាន់ភ្ញៀវតាមលេខសម្គាល់ ID\n"
            "• /broadcast &lt;សារ&gt; - ផ្ញើសារប្រកាសដំណឹងជូនភ្ញៀវទាំងអស់\n"
            "• /autoreply on ឬ off - បើក ឬបិទការឆ្លើយតបស្វ័យប្រវត្តិ\n"
            "• /setwelcome &lt;សារ&gt; - កំណត់សារស្វាគមន៍ថ្មី\n"
            "• /setautoreply &lt;សារ&gt; - កំណត់សារ Auto-reply ថ្មី\n"
            "• /help - បង្ហាញជំនួយនេះឡើងវិញ"
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
        return

    # Customer handling
    database.save_or_update_user(user.id, user.first_name, user.last_name, user.username)

    # Show welcome message once every 24 hours per user ID
    if database.should_send_autoreply(user.id, COOLDOWN_MINUTES):
        welcome_msg = database.get_setting("welcome_message")
        await send_welcome_or_autoreply(update, welcome_msg)
        database.record_autoreply(user.id)
    else:
        await update.message.reply_text("👋 សូមផ្ញើសារ ឬសំណួររបស់លោកអ្នកមកទីនេះ ក្រុមការងារយើងនឹងឆ្លើយតបជូនឆាប់ៗនេះ។ 🙏")

    # Notify admins about new user start
    customer_info = (
        f"🔔 <b>ភ្ញៀវថ្មីបានចុច /start</b>\n"
        f"👤 ឈ្មោះ: <b>{user.full_name}</b>\n"
        f"🆔 ID: <code>{user.id}</code> (ចុចលើលេខដើម្បី Copy)\n"
        f"🌐 Username: @{user.username if user.username else 'គ្មាន'}\n"
        f"📋 ឆ្លើយតបរហ័ស៖ <code>/reply {user.id} </code>"
    )
    for admin_id in ADMIN_IDS:
        try:
            msg = await context.bot.send_message(
                chat_id=admin_id,
                text=customer_info,
                parse_mode=ParseMode.HTML,
                reply_markup=get_quick_reply_keyboard(user.id)
            )
            database.save_message_mapping(msg.message_id, user.id, update.message.message_id)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        await start_command(update, context)
    else:
        await update.message.reply_text(
            "សូមផ្ញើសារ ឬសំណួររបស់លោកអ្នកមកទីនេះ ក្រុមការងារយើងនឹងឆ្លើយតបជូនលោកអ្នកឆាប់ៗនេះ។ 🙏"
        )


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    total = database.get_user_count()
    users = database.get_all_users()[:5]

    text = f"📊 <b>ស្ថិតិអ្នកប្រើប្រាស់</b>\n\nចំនួនភ្ញៀវសរុប៖ <b>{total}</b> នាក់\n\n"
    if users:
        text += "👥 <b>ភ្ញៀវសកម្ម ៥ នាក់ចុងក្រោយ៖</b>\n"
        for idx, u in enumerate(users, 1):
            name = f"{u['first_name']} {u['last_name'] or ''}".strip()
            uname = f"@{u['username']}" if u['username'] else "គ្មាន username"
            text += f"{idx}. <b>{name}</b> ({uname})\n   🆔 ID: <code>{u['user_id']}</code> | <code>/reply {u['user_id']} </code>\n"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def autoreply_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        current = database.get_setting("auto_reply_enabled", "true")
        status = "🟢 បើក (ON)" if current.lower() == "true" else "🔴 បិទ (OFF)"
        await update.message.reply_text(
            f"ស្ថានភាព Auto-reply បច្ចុប្បន្ន៖ {status}\n\nប្រើ <code>/autoreply on</code> ឬ <code>/autoreply off</code> ដើម្បីប្ដូរ។",
            parse_mode=ParseMode.HTML
        )
        return

    action = context.args[0].lower()
    if action in ["on", "enable", "1", "true"]:
        database.set_setting("auto_reply_enabled", "true")
        await update.message.reply_text("✅ បានបើកមុខងារ Auto-reply រួចរាល់។")
    elif action in ["off", "disable", "0", "false"]:
        database.set_setting("auto_reply_enabled", "false")
        await update.message.reply_text("🛑 បានបិទមុខងារ Auto-reply រួចរាល់។")
    else:
        await update.message.reply_text("⚠️ សូមប្រើ៖ <code>/autoreply on</code> ឬ <code>/autoreply off</code>", parse_mode=ParseMode.HTML)


async def set_welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text = update.message.text.split(maxsplit=1)
    if len(text) < 2:
        current = database.get_setting("welcome_message")
        await update.message.reply_text(
            f"📝 <b>សារស្វាគមន៍បច្ចុប្បន្ន៖</b>\n{current}\n\n"
            f"ដើម្បីកែប្រែ សូមវាយ៖ <code>/setwelcome សារថ្មីរបស់អ្នក...</code>",
            parse_mode=ParseMode.HTML
        )
        return

    new_msg = text[1].strip()
    database.set_setting("welcome_message", new_msg)
    await update.message.reply_text("✅ បានផ្លាស់ប្ដូរសារស្វាគមន៍ដោយជោគជ័យ!")


async def set_autoreply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text = update.message.text.split(maxsplit=1)
    if len(text) < 2:
        current = database.get_setting("auto_reply_message")
        await update.message.reply_text(
            f"📝 <b>សារ Auto-reply បច្ចុប្បន្ន៖</b>\n{current}\n\n"
            f"ដើម្បីកែប្រែ សូមវាយ៖ <code>/setautoreply សារថ្មីរបស់អ្នក...</code>",
            parse_mode=ParseMode.HTML
        )
        return

    new_msg = text[1].strip()
    database.set_setting("auto_reply_message", new_msg)
    await update.message.reply_text("✅ បានផ្លាស់ប្ដូរសារ Auto-reply ដោយជោគជ័យ!")


async def reply_by_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ ទម្រង់ប្រើ៖ <code>/reply &lt;User_ID&gt; &lt;សារ&gt;</code>\nឧទាហរណ៍៖ <code>/reply 12345678 សួស្ដីបាទ!</code>",
            parse_mode=ParseMode.HTML
        )
        return

    target_id_str = context.args[0]
    if not target_id_str.isdigit():
        await update.message.reply_text("⚠️ User ID ត្រូវតែជាលេខសុទ្ធ។")
        return

    target_id = int(target_id_str)
    message_text = " ".join(context.args[1:])

    try:
        await context.bot.send_message(chat_id=target_id, text=message_text)
        await update.message.reply_text(f"✅ បានផ្ញើសារទៅកាន់ ID <code>{target_id}</code> រួចរាល់!", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ មិនអាចផ្ញើសារបានទេ៖ {e}")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text_parts = update.message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        await update.message.reply_text(
            "⚠️ ទម្រង់ប្រើ៖ <code>/broadcast &lt;សារដែលចង់ប្រកាស&gt;</code>",
            parse_mode=ParseMode.HTML
        )
        return

    broadcast_text = text_parts[1].strip()
    users = database.get_all_users()
    total = len(users)

    if total == 0:
        await update.message.reply_text("មិនទាន់មានភ្ញៀវនៅក្នុងប្រព័ន្ធនៅឡើយទេ។")
        return

    status_msg = await update.message.reply_text(f"⏳ កំពុងផ្ញើសារប្រកាសទៅកាន់ភ្ញៀវចំនួន {total} នាក់...")

    success = 0
    failed = 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u["user_id"], text=broadcast_text)
            success += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"📢 <b>ការប្រកាសដំណឹងបានបញ្ចប់</b>\n\n"
        f"✅ ជោគជ័យ៖ {success} នាក់\n"
        f"❌ បរាជ័យ (Block Bot/លុបគណនី)៖ {failed} នាក់",
        parse_mode=ParseMode.HTML
    )


# --- Message Relaying Handlers ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id

    # 1. ADMIN HANDLING (Admin replying to a customer message)
    if is_admin(user.id):
        # Check if this is a reply to a forwarded/copied customer message
        if update.message.reply_to_message:
            replied_msg_id = update.message.reply_to_message.message_id
            customer_chat_id, customer_msg_id = database.get_customer_by_admin_msg(replied_msg_id)

            if customer_chat_id:
                # Check if Admin sent a quick template shortcut (e.g. 1-8 or /1-/8)
                text_content = (update.message.text or "").strip()
                clean_shortcut = text_content.lstrip("/").strip()
                if clean_shortcut in QUICK_REPLIES:
                    template_text = QUICK_REPLIES[clean_shortcut]
                    try:
                        await context.bot.send_message(chat_id=customer_chat_id, text=template_text)
                        await update.message.reply_text(
                            f"✅ បានឆ្លើយតប Quick Reply #{clean_shortcut} ជូនភ្ញៀវ៖\n<i>\"{template_text}\"</i>",
                            parse_mode=ParseMode.HTML,
                            quote=True
                        )
                        return
                    except Exception as e:
                        logger.error(f"Error sending quick reply template: {e}")
                        await update.message.reply_text(f"❌ មិនអាចផ្ញើជូនភ្ញៀវបានទេ៖ {e}", quote=True)
                        return

                try:
                    # Forward/Copy the admin's reply directly to the customer
                    await context.bot.copy_message(
                        chat_id=customer_chat_id,
                        from_chat_id=chat_id,
                        message_id=update.message.message_id
                    )
                    await update.message.reply_text("✅ បានឆ្លើយតបជូនភ្ញៀវរួចរាល់!", quote=True)
                except Exception as e:
                    logger.error(f"Error copying message to customer {customer_chat_id}: {e}")
                    err_str = str(e)
                    if "USER_RESTRICTS_VOICE_MESSAGES" in err_str or "VOICE_MESSAGES_FORBIDDEN" in err_str:
                        await update.message.reply_text("⚠️ ភ្ញៀវបានកំណត់បិទការទទួលសារសំឡេង (Voice Restricted)។ សូមវាយជាអក្សរជំនួសវិញ!", quote=True)
                    else:
                        await update.message.reply_text(f"❌ មិនអាចផ្ញើជូនភ្ញៀវបានទេ៖ {e}", quote=True)
            else:
                await update.message.reply_text(
                    "⚠️ មិនអាចស្គាល់ភ្ញៀវសម្រាប់សារនេះទេ (ប្រហែលជាសារចាស់ពេក ឬមិនមែនជាសាររបស់ភ្ញៀវ)។\n"
                    "លោកអ្នកអាចប្រើ <code>/reply &lt;ID&gt; &lt;សារ&gt;</code> ជំនួសវិញបាន។",
                    parse_mode=ParseMode.HTML,
                    quote=True
                )
        return

    # 2. CUSTOMER HANDLING (Customer sending message to Bot)
    database.save_or_update_user(user.id, user.first_name, user.last_name, user.username)

    # Check and trigger auto-reply
    if database.should_send_autoreply(user.id, COOLDOWN_MINUTES):
        auto_reply_text = database.get_setting("auto_reply_message")
        try:
            await send_welcome_or_autoreply(update, auto_reply_text)
            database.record_autoreply(user.id)
        except Exception as e:
            logger.error(f"Error sending auto reply: {e}")

    # Relay customer message to Admin(s)
    customer_name = user.full_name
    username_str = f"@{user.username}" if user.username else "គ្មាន username"

    # Identify message type for clear Admin notification
    msg_type_str = "សារអត្ថបទ"
    if update.message.voice:
        msg_type_str = "🎙 សារសំឡេង (Voice Message)"
    elif update.message.audio:
        msg_type_str = "🎵 ឯកសារចម្រៀង (Audio)"
    elif update.message.photo:
        msg_type_str = "🖼 រូបភាព (Photo)"
    elif update.message.video:
        msg_type_str = "🎥 វីដេអូ (Video)"
    elif update.message.video_note:
        msg_type_str = "⭕ វីដេអូមូល (Video Note)"
    elif update.message.document:
        msg_type_str = "📄 ឯកសារ (Document)"
    elif update.message.sticker:
        msg_type_str = "🌟 Sticker"

    header_text = (
        f"📩 <b>សារថ្មីពីភ្ញៀវ ({msg_type_str})៖</b>\n"
        f"👤 ឈ្មោះ: <b>{customer_name}</b> ({username_str})\n"
        f"🆔 ID: <code>{user.id}</code> (ចុចលើលេខដើម្បី Copy)\n"
        f"📋 ឆ្លើយតបរហ័ស៖ <code>/reply {user.id} </code>\n\n"
        f"⚡ <b>ចុចលើប៊ូតុងខាងក្រោមដើម្បីផ្ញើ Quick Reply ភ្លាមៗ៖</b>"
    )

    for admin_id in ADMIN_IDS:
        try:
            # Send info header with Quick Reply buttons
            info_msg = await context.bot.send_message(
                chat_id=admin_id,
                text=header_text,
                parse_mode=ParseMode.HTML,
                reply_markup=get_quick_reply_keyboard(user.id)
            )
            database.save_message_mapping(info_msg.message_id, user.id, update.message.message_id)

            try:
                # Copy actual message (supports text, photo, audio, voice, video, document, sticker...)
                copied_msg = await context.bot.copy_message(
                    chat_id=admin_id,
                    from_chat_id=chat_id,
                    message_id=update.message.message_id
                )
                database.save_message_mapping(copied_msg.message_id, user.id, update.message.message_id)
            except Exception as copy_err:
                logger.warning(f"copy_message failed: {copy_err}. Attempting fallback...")
                if "voice_messages_forbidden" in str(copy_err).lower():
                    if update.message.voice:
                        voice_file = await context.bot.get_file(update.message.voice.file_id)
                        voice_bytes = await voice_file.download_as_bytearray()
                        bio = io.BytesIO(voice_bytes)
                        bio.name = f"voice_message_{user.id}.ogg"
                        audio_msg = await context.bot.send_audio(
                            chat_id=admin_id,
                            audio=bio,
                            duration=update.message.voice.duration,
                            title=f"Voice ពី {customer_name}",
                            performer="Customer Voice Note",
                            caption="🎙 <i>(សារសំឡេងនេះត្រូវបានផ្ញើជា Audio ជំនួស ព្រោះគណនី Admin កំណត់បិទ Voice ក្នុង Privacy)</i>",
                            parse_mode=ParseMode.HTML
                        )
                        database.save_message_mapping(audio_msg.message_id, user.id, update.message.message_id)
                    elif update.message.video_note:
                        vn_file = await context.bot.get_file(update.message.video_note.file_id)
                        vn_bytes = await vn_file.download_as_bytearray()
                        bio = io.BytesIO(vn_bytes)
                        bio.name = f"video_note_{user.id}.mp4"
                        vn_msg = await context.bot.send_video(
                            chat_id=admin_id,
                            video=bio,
                            caption="⭕ <i>(វីដេអូមូលត្រូវបានផ្ញើជា Video file ជំនួស)</i>",
                            parse_mode=ParseMode.HTML
                        )
                        database.save_message_mapping(vn_msg.message_id, user.id, update.message.message_id)
                    else:
                        raise copy_err
                else:
                    raise copy_err

        except Exception as e:
            logger.error(f"Failed to forward customer message to admin {admin_id}: {e}")


async def templates_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    msg = "⚡ <b>បញ្ជី Quick Reply Templates ទាំង ១១៖</b>\n\n"
    for k, v in QUICK_REPLIES.items():
        msg += f"<b>{k}️⃣:</b> <i>\"{v}\"</i>\n\n"
    msg += (
        "👉 <b>វិធីប្រើ៖</b>\n"
        "1. ចុចលើប៊ូតុង Quick Reply នៅខាងក្រោមសារភ្ញៀវភ្លាមៗ\n"
        "2. ឬចុច <b>Reply</b> លើសារភ្ញៀវ រួចវាយលេខ <code>1</code> ដល់ <code>11</code>"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def quick_reply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    data = query.data
    if not data or not data.startswith("qr:"):
        return

    parts = data.split(":")
    if len(parts) != 3:
        return

    customer_id = int(parts[1])
    template_num = parts[2]

    template_text = QUICK_REPLIES.get(template_num)
    if not template_text:
        return

    try:
        await context.bot.send_message(chat_id=customer_id, text=template_text)
        await query.message.reply_text(
            f"✅ <b>បានផ្ញើ Quick Reply #{template_num} ជូនភ្ញៀវរួចរាល់៖</b>\n<i>\"{template_text}\"</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error sending quick reply via button: {e}")
        await query.message.reply_text(f"❌ មិនអាចផ្ញើជូនភ្ញៀវបានទេ៖ {e}")


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is online and running 24/7!")

    def log_message(self, format, *args):
        pass  # Quiet logs


def run_health_server(port: int):
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health check server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")


def main():
    if not BOT_TOKEN:
        print("❌ កំហុស៖ មិនទាន់បានកំណត់ BOT_TOKEN នៅក្នុងឯកសារ .env នៅឡើយទេ។")
        return

    # Start dummy web server for Cloud Hosting (Render / Koyeb / Railway)
    port_env = os.getenv("PORT", "8080")
    threading.Thread(target=run_health_server, args=(int(port_env),), daemon=True).start()

    # Initialize database
    database.init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("templates", templates_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("autoreply", autoreply_toggle))
    app.add_handler(CommandHandler("setwelcome", set_welcome_command))
    app.add_handler(CommandHandler("setautoreply", set_autoreply_command))
    app.add_handler(CommandHandler("reply", reply_by_id_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))

    # Inline Button Callback (Quick Replies)
    app.add_handler(CallbackQueryHandler(quick_reply_callback, pattern=r"^qr:"))

    # All regular messages (text, photos, files, voice, etc.)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("🤖 Bot កំពុងដំណើរការ... ចុច Ctrl+C ដើម្បីបញ្ឈប់។")
    app.run_polling()


if __name__ == "__main__":
    main()
