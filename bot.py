import json
import os
import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================================================
# تنظیمات اصلی
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is not set"
    )

CHANNEL_USERNAME = "@wallpaperrrforyou"

STORAGE_CHAT_ID = -1004261540763

BOT_USERNAME = "wallpaperrrforyoubot"

# آیدی عددی صاحب ربات
OWNER_ID = 5176148280


# =========================================================
# فایل‌های ذخیره اطلاعات
# =========================================================

WALLPAPERS_FILE = "wallpapers.json"
PENDING_FILE = "pending.json"
QUEUE_FILE = "publish_queue.json"
STATUS_FILE = "bot_status.json"


# =========================================================
# توابع ذخیره و بارگذاری
# =========================================================

def load_json(filename, default):

    if not os.path.exists(filename):
        return default

    try:

        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:

        return default


def save_json(filename, data):

    with open(filename, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# اطلاعات والپیپرها
# =========================================================

wallpapers = load_json(
    WALLPAPERS_FILE,
    {}
)

pending = load_json(
    PENDING_FILE,
    {}
)

publish_queue = load_json(
    QUEUE_FILE,
    []
)


# =========================================================
# وضعیت ربات
# =========================================================

bot_status = load_json(
    STATUS_FILE,
    {"online": True}
)


def is_bot_online():

    return bot_status.get(
        "online",
        True
    )


def set_bot_status(online):

    bot_status["online"] = online

    bot_status["updated_at"] = time.time()

    save_json(
        STATUS_FILE,
        bot_status
    )


# =========================================================
# پیام حالت آفلاین
# =========================================================

OFFLINE_TEXT = (
    "🔥⏳ ربات فعلاً در حال استراحته! 😴\n\n"
    "⚠️ سرویس دانلود موقتاً غیرفعاله.\n\n"
    "❤️ لطفاً حدود ۱ تا ۲ ساعت دیگه دوباره امتحان کن.\n\n"
    "🚀 به محض فعال شدن، دانلود دوباره در دسترس خواهد بود."
)


def get_offline_keyboard(wp_id):

    keyboard = [

        [
            InlineKeyboardButton(
                "🔥🔄 دوباره امتحان می‌کنم",
                callback_data=f"retry:{wp_id}"
            )
        ]

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# والپیپر قبلی
# =========================================================

if "wp_001" not in wallpapers:

    wallpapers["wp_001"] = {

        "photo": 7,

        "document": 8

    }

    save_json(
        WALLPAPERS_FILE,
        wallpapers
    )


# =========================================================
# ساخت ID جدید
# =========================================================

def get_next_wallpaper_id():

    numbers = []

    for wp_id in wallpapers.keys():

        if wp_id.startswith("wp_"):

            try:

                number = int(
                    wp_id.replace(
                        "wp_",
                        ""
                    )
                )

                numbers.append(
                    number
                )

            except ValueError:

                pass

    next_number = max(
        numbers,
        default=0
    ) + 1

    return f"wp_{next_number:03d}"


# =========================================================
# لینک دانلود بات
# =========================================================

def get_download_link(wp_id):

    return (
        f"https://t.me/"
        f"{BOT_USERNAME}"
        f"?start={wp_id}"
    )


# =========================================================
# ساخت دکمه دانلود
# =========================================================

def get_download_keyboard(wp_id):

    download_link = get_download_link(
        wp_id
    )

    keyboard = [

        [

            InlineKeyboardButton(
                "🔥دانلود فایل اصلی والپیپر باکیفیت بالا و اورجینال🔥",
                url=download_link
            )

        ]

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# بررسی عضویت
# =========================================================

async def check_membership(
    user_id,
    context
):

    try:

        member = await context.bot.get_chat_member(

            chat_id=CHANNEL_USERNAME,

            user_id=user_id

        )

        return member.status in [

            "member",
            "administrator",
            "creator"

        ]

    except Exception:

        return False


# =========================================================
# ارسال والپیپر
# =========================================================

async def send_wallpaper(
    chat_id,
    wp_id,
    context
):

    if wp_id not in wallpapers:

        await context.bot.send_message(

            chat_id=chat_id,

            text="❌ این والپیپر پیدا نشد."

        )

        return

    data = wallpapers[wp_id]

    photo_message_id = data.get(
        "photo"
    )

    document_message_id = data.get(
        "document"
    )

    # ارسال عکس
    if photo_message_id:

        await context.bot.copy_message(

            chat_id=chat_id,

            from_chat_id=STORAGE_CHAT_ID,

            message_id=photo_message_id

        )

    # ارسال فایل اصلی
    if document_message_id:

        await context.bot.copy_message(

            chat_id=chat_id,

            from_chat_id=STORAGE_CHAT_ID,

            message_id=document_message_id

        )


# =========================================================
# /OFF
# =========================================================

async def bot_off(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    # فقط صاحب ربات
    if user.id != OWNER_ID:

        await update.message.reply_text(

            "⛔ این دستور فقط برای مدیر ربات قابل استفاده است."

        )

        return

    if not is_bot_online():

        await update.message.reply_text(

            "🔴🔥 ربات از قبل در حالت تعطیلیه!\n\n"
            "کاربران فعلاً پیام استراحت دریافت می‌کنن. 😴"

        )

        return

    set_bot_status(False)

    await update.message.reply_text(

        "🔴🔥 حالت تعطیلی فعال شد!\n\n"
        "😴 ربات فعلاً به کاربران فایل ارسال نمی‌کنه.\n\n"
        "📢 کاربران پیام موقتاً آفلاین بودن ربات رو دریافت می‌کنن.\n\n"
        "🟢 هر وقت آماده بودی فقط /on رو بزن."

    )


# =========================================================
# /ON
# =========================================================

async def bot_on(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    # فقط صاحب ربات
    if user.id != OWNER_ID:

        await update.message.reply_text(

            "⛔ این دستور فقط برای مدیر ربات قابل استفاده است."

        )

        return

    if is_bot_online():

        await update.message.reply_text(

            "🟢🔥 ربات همین الان هم فعاله!\n\n"
            "🚀 سیستم دانلود آماده دریافت درخواست‌هاست."

        )

        return

    set_bot_status(True)

    await update.message.reply_text(

        "🟢🔥 ربات دوباره فعال شد!\n\n"
        "🚀 سیستم دانلود با موفقیت آنلاین شد.\n\n"
        "❤️ کاربران می‌تونن دوباره والپیپرها رو دریافت کنن."

    )


# =========================================================
# /STATUS
# =========================================================

async def bot_status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    if user.id != OWNER_ID:

        await update.message.reply_text(

            "⛔ این دستور فقط برای مدیر ربات قابل استفاده است."

        )

        return

    if is_bot_online():

        await update.message.reply_text(

            "🟢🔥 وضعیت ربات: آنلاین\n\n"
            "🚀 دانلودها فعال هستند."

        )

    else:

        await update.message.reply_text(

            "🔴🔥 وضعیت ربات: آفلاین\n\n"
            "😴 کاربران پیام تعطیلی دریافت می‌کنند.\n\n"
            "🟢 برای فعال‌کردن دوباره: /on"

        )


# =========================================================
# /start
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    args = context.args

    # =====================================================
    # اگر لینک والپیپر باشد
    # =====================================================

    if args:

        wp_id = args[0]

        if wp_id not in wallpapers:

            await update.message.reply_text(

                "❌ این والپیپر پیدا نشد."

            )

            return

        # =================================================
        # بررسی حالت آفلاین
        # =================================================

        if not is_bot_online():

            await update.message.reply_text(

                OFFLINE_TEXT,

                reply_markup=get_offline_keyboard(
                    wp_id
                )

            )

            return

        # =================================================
        # بررسی عضویت
        # =================================================

        is_member = await check_membership(

            user.id,

            context

        )

        if is_member:

            await update.message.reply_text(

                "✅ عضویت شما تأیید شد! 🎉\n\n"
                "🔥 در حال ارسال والپیپر..."

            )

            await send_wallpaper(

                update.effective_chat.id,

                wp_id,

                context

            )

            return

        # =================================================
        # کاربر عضو نیست
        # =================================================

        keyboard = [

            [

                InlineKeyboardButton(

                    "📢 عضویت در کانال",

                    url=(
                        f"https://t.me/"
                        f"{CHANNEL_USERNAME.replace('@', '')}"
                    )

                )

            ],

            [

                InlineKeyboardButton(

                    "✅ بررسی عضویت",

                    callback_data=f"check:{wp_id}"

                )

            ]

        ]

        await update.message.reply_text(

            "🔒 برای دریافت فایل اصلی والپیپر، "
            "ابتدا باید عضو کانال شوید.\n\n"

            "1️⃣ روی «عضویت در کانال» بزنید.\n"
            "2️⃣ عضو کانال شوید.\n"
            "3️⃣ سپس روی «بررسی عضویت» بزنید. ❤️",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )

        )

        return

    # =====================================================
    # /start معمولی
    # =====================================================

    if not is_bot_online():

        await update.message.reply_text(

            OFFLINE_TEXT

        )

        return

    await update.message.reply_text(

        "👋 سلام! ❤️\n\n"

        "🔥 به ربات دانلود والپیپر خوش آمدید.\n\n"

        "📱 برای دریافت والپیپر اصلی و باکیفیت، "
        "از لینک دانلود مربوط به هر والپیپر استفاده کنید."

    )


# =========================================================
# بررسی عضویت با دکمه
# =========================================================

async def check_membership_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    data = query.data

    if not data.startswith("check:"):

        return

    wp_id = data.split(
        ":",
        1
    )[1]

    # =====================================================
    # اگر ربات آفلاین باشد
    # =====================================================

    if not is_bot_online():

        await query.edit_message_text(

            OFFLINE_TEXT,

            reply_markup=get_offline_keyboard(
                wp_id
            )

        )

        return

    # =====================================================
    # بررسی عضویت
    # =====================================================

    is_member = await check_membership(

        user_id,

        context

    )

    if not is_member:

        keyboard = [

            [

                InlineKeyboardButton(

                    "📢 عضویت در کانال",                
                    url=(
                        f"https://t.me/"                                        f"{CHANNEL_USERNAME.replace('@', '')}"
                    )

                )

            ],

            [                                           
                InlineKeyboardButton(

                    "🔄 بررسی مجدد",

                    callback_data=f"check:{wp_id}"

                )

            ]

        ]

        await query.edit_message_text(

            "❌ هنوز عضویت شما تأیید نشده است.\n\n"

            "ابتدا عضو کانال شوید و سپس دوباره "
            "روی «بررسی مجدد» بزنید.",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
                                                                )

        return                                          
    # =====================================================
    # عضویت تأیید شد
    # =====================================================

    await query.edit_message_text(

        "✅ عضویت شما تأیید شد! 🎉\n\n"
        "🔥 در حال ارسال والپیپر..."

    )

    await send_wallpaper(                               
        query.message.chat_id,
                                                                wp_id,

        context

    )


# =========================================================                                                     # دکمه دوباره امتحان کن
# =========================================================                                                     
async def retry_download_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    data = query.data

    if not data.startswith("retry:"):

        return

    wp_id = data.split(
        ":",
        1
    )[1]

    # =====================================================
    # بررسی وجود والپیپر
    # =====================================================

    if wp_id not in wallpapers:                         
        await query.edit_message_text(
                                                                    "❌ این والپیپر پیدا نشد."

        )

        return

    # =====================================================
    # هنوز آفلاین است
    # =====================================================

    if not is_bot_online():

        await query.answer(

            "🔴 هنوز آفلاین هستیم؛ بعداً دوباره امتحان کن ❤️",
                                                                    show_alert=True

        )                                               
        return

    # =====================================================
    # ربات آنلاین شده
    # =====================================================

    is_member = await check_membership(

        user_id,

        context

    )

    if is_member:

        await query.edit_message_text(

            "🟢🔥 ربات دوباره فعال شده!\n\n"
            "✅ عضویت شما تأیید شد.\n"
            "🚀 در حال ارسال والپیپر..."

        )

        await send_wallpaper(
                                                                    query.message.chat_id,

            wp_id,                                      
            context

        )

        return
                                                            # =====================================================
    # هنوز عضو نیست
    # =====================================================

    keyboard = [

        [

            InlineKeyboardButton(

                "📢 عضویت در کانال",

                url=(
                    f"https://t.me/"
                    f"{CHANNEL_USERNAME.replace('@', '')}"
                )

            )

        ],                                              
        [
                                                                    InlineKeyboardButton(

                "✅ بررسی عضویت",

                callback_data=f"check:{wp_id}"

            )

        ]

    ]

    await query.edit_message_text(

        "🔒 ربات دوباره فعال شده! 🔥\n\n"

        "اما برای دریافت فایل اصلی، "
        "ابتدا باید عضو کانال شوید. ❤️",
                                                                reply_markup=InlineKeyboardMarkup(
            keyboard
        )                                               
    )


# =========================================================
# دریافت عکس از مخزن
# =========================================================

async def storage_photo_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.effective_message

    if not message:
        return

    if message.chat.id != STORAGE_CHAT_ID:
        return

    if not message.photo:
        return

    user_id = (
        message.from_user.id
        if message.from_user
        else 0
    )

    photo = message.photo[-1]

    pending[str(user_id)] = {
                                                                "photo": message.message_id,

        "time": time.time()                             
    }

    save_json(

        PENDING_FILE,

        pending

    )

    print(                                              
        f"📸 عکس جدید در مخزن ثبت شد | "
        f"message_id={message.message_id}"              
    )


# =========================================================
# دریافت فایل از مخزن
# =========================================================

async def storage_document_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):                                                      
    message = update.effective_message

    if not message:
        return

    if message.chat.id != STORAGE_CHAT_ID:
        return

    if not message.document:
        return

    user_id = (
        message.from_user.id                                    if message.from_user
        else 0
    )                                                   
    user_key = str(user_id)

    if user_key not in pending:

        print(
            "⚠️ فایل دریافت شد ولی عکس "
            "منتظر جفت شدن وجود ندارد."
        )

        return

    pending_data = pending[user_key]

    if time.time() - pending_data["time"] > 600:

        del pending[user_key]

        save_json(

            PENDING_FILE,

            pending

        )

        print(
            "⚠️ عکس قبلی بیش از ۱۰ دقیقه قدیمی بود."
        )

        return                                          
    photo_message_id = pending_data["photo"]
                                                            document_message_id = message.message_id

    # =====================================================
    # ساخت ID جدید
    # =====================================================

    wp_id = get_next_wallpaper_id()

    wallpapers[wp_id] = {

        "photo": photo_message_id,

        "document": document_message_id

    }

    save_json(

        WALLPAPERS_FILE,

        wallpapers

    )

    # =====================================================
    # اضافه کردن به صف انتشار
    # =====================================================

    publish_queue.append(
        wp_id
    )

    save_json(

        QUEUE_FILE,

        publish_queue

    )

    # =====================================================
    # حذف pending
    # =====================================================

    del pending[user_key]

    save_json(

        PENDING_FILE,

        pending
                                                            )

    print(                                                      f"✅ والپیپر جدید ثبت شد: {wp_id}"
    )

    print(
        f"📸 Photo message ID: {photo_message_id}"
    )

    print(
        f"📄 Document message ID: {document_message_id}"
    )

    print(
        f"🔗 لینک: {get_download_link(wp_id)}"
    )


# =========================================================                                                     # وقتی عکس در کانال منتشر شد
# =========================================================

async def channel_photo_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.effective_message

    if not message:
        return

    if message.chat.username:

        channel_username = (
            "@" + message.chat.username
        )

    else:

        channel_username = ""
                                                            if (
        channel_username.lower()
        != CHANNEL_USERNAME.lower()
    ):

        return
                                                            if not message.photo:
        return
                                                            # =====================================================
    # اگر والپیپر در صف انتشار وجود دارد
    # =====================================================

    if not publish_queue:

        print(
            "ℹ️ عکس کانال دریافت شد ولی "
            "والپیپر منتظری در صف نیست."
        )

        return

    wp_id = publish_queue.pop(0)

    save_json(                                          
        QUEUE_FILE,

        publish_queue

    )

    keyboard = get_download_keyboard(
        wp_id
    )

    try:

        await context.bot.edit_message_reply_markup(

            chat_id=message.chat.id,

            message_id=message.message_id,

            reply_markup=keyboard

        )

        print(                                                      f"✅ دکمه دانلود برای {wp_id} "
            f"به پست کانال اضافه شد."
        )

    except Exception as e:
                                                                print(
            f"❌ خطا در اضافه کردن دکمه: {e}"
        )                                               
        publish_queue.insert(
            0,
            wp_id
        )

        save_json(

            QUEUE_FILE,

            publish_queue

        )


# =========================================================                                                     # دستور /list
# =========================================================

async def list_wallpapers(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not wallpapers:

        await update.message.reply_text(

            "هنوز والپیپری ثبت نشده است."

        )

        return

    items = list(
        wallpapers.items()
    )

    items = items[-20:]

    text = "📚 آخرین والپیپرها:\n\n"
                                                            for wp_id, data in items:

        text += (                                       
            f"🖼 {wp_id}\n"

            f"🔗 {get_download_link(wp_id)}\n\n"

        )

    await update.message.reply_text(
        text
    )


# =========================================================
# مدیریت خطا                                            # =========================================================
                                                        async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "❌ ERROR:",
        context.error
    )


# =========================================================
# اجرای ربات
# =========================================================
                                                        def main():

    print(                                                      "======================================"
    )

    print(
        "🤖 Wallpaper Bot"
    )

    print(
        "======================================"
    )

    print(
        "🚀 Bot is starting..."
    )

    print("")
                                                            application = (

        Application.builder()                           
        .token(TOKEN)

        .build()

    )

    # =====================================================
    # /start
    # =====================================================

    application.add_handler(

        CommandHandler(
            "start",
            start
        )

    )

    # =====================================================
    # /off
    # =====================================================

    application.add_handler(

        CommandHandler(
            "off",                                                  bot_off
        )
                                                            )

    # =====================================================
    # /on
    # =====================================================

    application.add_handler(

        CommandHandler(
            "on",
            bot_on                                              )

    )

    # =====================================================
    # /status
    # =====================================================

    application.add_handler(

        CommandHandler(
            "status",
            bot_status_command
        )

    )

    # =====================================================
    # /list
    # =====================================================

    application.add_handler(

        CommandHandler(
            "list",
            list_wallpapers
        )

    )

    # =====================================================
    # بررسی عضویت
    # =====================================================                                                     
    application.add_handler(
                                                                CallbackQueryHandler(

            check_membership_callback,

            pattern=r"^check:"

        )

    )

    # =====================================================
    # دکمه دوباره امتحان کن
    # =====================================================

    application.add_handler(

        CallbackQueryHandler(
                                                                    retry_download_callback,

            pattern=r"^retry:"

        )
                                                            )

    # =====================================================
    # عکس‌های مخزن
    # =====================================================

    application.add_handler(

        MessageHandler(

            filters.Chat(STORAGE_CHAT_ID)
            & filters.PHOTO,

            storage_photo_handler

        )

    )

    # =====================================================
    # فایل‌های مخزن
    # =====================================================

    application.add_handler(                            
        MessageHandler(
                                                                    filters.Chat(STORAGE_CHAT_ID)
            & filters.Document.ALL,

            storage_document_handler

        )

    )

    # =====================================================
    # عکس‌های کانال
    # =====================================================

    application.add_handler(
                                                                MessageHandler(

            filters.PHOTO,                              
            channel_photo_handler

        )

    )

    # =====================================================
    # خطاها
    # =====================================================

    application.add_error_handler(
        error_handler
    )

    print(
        "======================================"
    )

    if is_bot_online():
                                                                print(
            "🟢🔥 Status: ONLINE"
        )

    else:

        print(
            "🔴🔥 Status: OFFLINE"
        )

    print(
        "======================================"
    )

    print(
        "✅ Bot is running..."
    )

    print("")

    application.run_polling(

        allowed_updates=Update.ALL_TYPES

    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()
