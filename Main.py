import os
import datetime
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# تنظیمات
BOT_TOKEN = os.getenv('BOT_TOKEN', '8498872124:AAHS37lR6_GtqZkW3lgsr-c_IClUXB51kbY')
ADMIN_CHAT_ID = 8241614823

# حالت‌های گفتگو
(
    GET_NAME, GET_AGE, GET_CITY, 
    GET_PAIN_LOCATION, GET_PAIN_INTENSITY, GET_PAIN_DURATION, 
    GET_MRI_STATUS, CHOOSE_DESCRIPTION_TYPE, GET_PAIN_DESCRIPTION, GET_VOICE_DESCRIPTION
) = range(10)

user_sessions = {}

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def send_to_admin(context, message, voice=None, photo=None):
    try:
        if voice:
            await context.bot.send_voice(chat_id=ADMIN_CHAT_ID, voice=voice, caption=message)
        elif photo:
            await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=message)
        else:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
        return True
    except Exception as e:
        logging.error(f"خطا در ارسال به ادمین: {e}")
        return False

def get_user_info(update):
    user = update.message.from_user
    return f"👤 کاربر: {user.first_name}\n🆔 آیدی: @{user.username or 'ندارد'}\n📞 آیدی عددی: {user.id}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    user_sessions[user_id] = {
        'user_info': get_user_info(update),
        'start_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    welcome_text = (
        "🌟 **به ربات مشاوره پزشکی پرسیس خوش آمدید!** 🌟\n\n"
        "🏥 **درباره ما:**\n"
        "• ۱۲ سال تجربه در زمینه تجهیزات جراحی مغز و ستون فقرات\n"
        "• همکاری با برترین متخصصان کشور\n\n"
        "📋 **روند ثبت اطلاعات:**\n"
        "شما در ۹ مرحله ساده اطلاعات لازم را وارد می‌کنید.\n\n"
        "🔸 **مرحله ۱ از ۹:**\n"
        "**لطفاً نام و نام خانوادگی خود را وارد کنید:**"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=ReplyKeyboardRemove())
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_sessions[user_id]['name'] = update.message.text
    await update.message.reply_text("🎂 **لطفاً سن خود را وارد کنید:**")
    return GET_AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_sessions[user_id]['age'] = update.message.text
    await update.message.reply_text("🏙️ **لطفاً شهر خود را وارد کنید:**")
    return GET_CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_sessions[user_id]['city'] = update.message.text
    await update.message.reply_text("📍 **لطفاً محل دقیق درد خود را وارد کنید:**")
    return GET_PAIN_LOCATION

async def get_pain_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_sessions[user_id]['pain_location'] = update.message.text
    await update.message.reply_text("📊 **لطفاً شدت درد خود را از ۱ تا ۱۰ وارد کنید:**")
    return GET_PAIN_INTENSITY

async def get_pain_intensity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_sessions[user_id]['pain_intensity'] = update.message.text
    await update.message.reply_text("⏰ **لطفاً مدت زمان درد خود را وارد کنید:**")
    return GET_PAIN_DURATION

async def get_pain_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_sessions[user_id]['pain_duration'] = update.message.text
    
    keyboard = [["✅ بله، عکس MRI دارم", "❌ خیر، عکس MRI ندارم"], ["📋 نمی‌دانم چیست"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ **مدت زمان درد ثبت شد.**\n\n"
        "🔸 **مرحله ۷ از ۹:**\n"
        "**آیا قبلاً عکس MRI گرفته‌اید?**",
        reply_markup=reply_markup
    )
    return GET_MRI_STATUS

async def get_mri_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    choice = update.message.text
    
    if choice == "✅ بله، عکس MRI دارم":
        user_sessions[user_id]['mri_status'] = "دارد - منتظر ارسال"
        await update.message.reply_text(
            "✅ **وضعیت MRI ثبت شد.**\n\n"
            "📸 لطفاً عکس MRI خود را ارسال کنید:",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_MRI_STATUS
    elif choice == "❌ خیر، عکس MRI ندارم":
        user_sessions[user_id]['mri_status'] = "ندارد"
        await proceed_to_description(update)
        return CHOOSE_DESCRIPTION_TYPE
    else:
        user_sessions[user_id]['mri_status'] = "آشنایی ندارد"
        await proceed_to_description(update)
        return CHOOSE_DESCRIPTION_TYPE

async def handle_mri_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]
    
    if 'mri_photos' not in user_sessions[user_id]:
        user_sessions[user_id]['mri_photos'] = []
    
    user_sessions[user_id]['mri_photos'].append(photo.file_id)
    user_sessions[user_id]['mri_status'] = "دارد - ارسال شده"
    
    await update.message.reply_text("✅ عکس MRI دریافت شد. برای ادامه /start را بزنید.")
    return ConversationHandler.END

async def proceed_to_description(update: Update):
    keyboard = [["📝 توضیح متنی", "🎤 توضیح صوتی"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🔸 **مرحله ۸ از ۹:**\n"
        "**چگونه می‌خواهید درد خود را توصیف کنید?**",
        reply_markup=reply_markup
    )

async def choose_description_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    choice = update.message.text
    
    if choice == "📝 توضیح متنی":
        await update.message.reply_text(
            "🔸 **مرحله ۹ از ۹:**\n"
            "**لطفاً توضیحات کامل‌تری درباره شرایط خود بنویسید:**",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_PAIN_DESCRIPTION
    else:
        await update.message.reply_text(
            "🎤 لطفاً ویس خود را ارسال کنید:",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_VOICE_DESCRIPTION

async def get_pain_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_sessions[user_id]['pain_description'] = update.message.text
    user_sessions[user_id]['description_type'] = 'متنی'
    
    await complete_registration(update, context)
    return ConversationHandler.END

async def get_voice_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    voice = update.message.voice
    user_sessions[user_id]['voice_file_id'] = voice.file_id
    user_sessions[user_id]['description_type'] = 'صوتی'
    
    await complete_registration(update, context)
    return ConversationHandler.END

async def complete_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data = user_sessions[user_id]
    
    report = (
        "🆕 **درخواست مشاوره جدید**\n\n"
        f"👤 نام: {user_data.get('name', 'ثبت نشده')}\n"
        f"🎂 سن: {user_data.get('age', 'ثبت نشده')}\n"
        f"🏙️ شهر: {user_data.get('city', 'ثبت نشده')}\n"
        f"📍 محل درد: {user_data.get('pain_location', 'ثبت نشده')}\n"
        f"📊 شدت: {user_data.get('pain_intensity', 'ثبت نشده')}/۱۰\n"
        f"⏰ مدت: {user_data.get('pain_duration', 'ثبت نشده')}\n"
        f"📷 MRI: {user_data.get('mri_status', 'ثبت نشده')}\n"
        f"💬 نوع توضیح: {user_data.get('description_type', 'ثبت نشده')}\n\n"
        f"{user_data['user_info']}"
    )
    
    await send_to_admin(context, report)
    
    if user_data.get('mri_photos'):
        for photo_id in user_data['mri_photos']:
            await send_to_admin(context, "📸 عکس MRI", photo=photo_id)
    
    if user_data.get('voice_file_id'):
        await send_to_admin(context, "🎤 توضیح صوتی", voice=user_data['voice_file_id'])
    
    await update.message.reply_text("✅ **ثبت اطلاعات کامل شد! متخصصان به زودی تماس می‌گیرند.**")
    del user_sessions[user_id]

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await update.message.reply_text("❌ عملیات لغو شد. /start")
    return ConversationHandler.END

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GET_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            GET_PAIN_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pain_location)],
            GET_PAIN_INTENSITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pain_intensity)],
            GET_PAIN_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pain_duration)],
            GET_MRI_STATUS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_mri_status),
                MessageHandler(filters.PHOTO, handle_mri_photo)
            ],
            CHOOSE_DESCRIPTION_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_description_type)],
            GET_PAIN_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pain_description)],
            GET_VOICE_DESCRIPTION: [MessageHandler(filters.VOICE, get_voice_description)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    application.add_handler(conv_handler)
    
    print("✅ ربات فعال شد!")
    application.run_polling()

if __name__ == "__main__":
    main()