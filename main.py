
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

PHOTO, RESULT_TEXT, TOURNAMENT = range(3)
NAME, PHONE, NICK = range(3, 6)

GROUP_CHAT_USERNAME = "@resultssuperlauhe"
ADMIN_USERNAME = "@ivanryashin"
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 Добро пожаловать в бота турнира Суперлиги!\n\n"
        "📋 Команды:\n"
        "⚽ /result – 📸 Отправить результат\n"
        "📝 /register – ✍️ Подать заявку\n\n"
        "📌 Как работает /result:\n"
        "1️⃣ Отправьте скриншот матча\n"
        "2️⃣ Введите результат (например: Монако 3:0 Барселона)\n"
        "3️⃣ Выберите турнир\n"
        "📤 Результат будет опубликован в группе\n\n"
        "📌 Как работает /register:\n"
        "👤 Введите имя\n"
        "📞 Введите номер телефона\n"
        "🔗 Введите Telegram-ник\n"
        "📬 Заявка будет отправлена организатору"
    )
    await update.message.reply_text(text)

async def result_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Пожалуйста, отправьте скриншот матча")
    return PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1].file_id
    user_data[update.effective_user.id] = {'photo': photo}
    await update.message.reply_text("📝 Введите результат вручную (например: Монако 3:0 Барселона)")
    return RESULT_TEXT

async def handle_result_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['result_text'] = update.message.text

    keyboard = [[
        InlineKeyboardButton("Регулярный чемпионат", callback_data='Регулярный чемпионат'),
        InlineKeyboardButton("Кубок", callback_data='Кубок')
    ], [
        InlineKeyboardButton("Лига Чемпионов", callback_data='Лига Чемпионов'),
        InlineKeyboardButton("Лига Европы", callback_data='Лига Европы')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🏆 Выберите турнир:", reply_markup=reply_markup)
    return TOURNAMENT

async def handle_tournament(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tournament = query.data
    data = user_data.get(query.from_user.id, {})

    caption = f"📊 Результат матча: {data.get('result_text')}\n🏆 Турнир: {tournament}"
    await context.bot.send_photo(
        chat_id=GROUP_CHAT_USERNAME,
        photo=data.get('photo'),
        caption=caption
    )

    await query.edit_message_text("✅ Результат принят и отправлен в группу!")
    return ConversationHandler.END

async def application_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Введите своё имя:")
    return NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {'name': update.message.text}
    await update.message.reply_text("📞 Введите номер телефона:")
    return PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['phone'] = update.message.text
    await update.message.reply_text("🔗 Введите свой @ник в Telegram:")
    return NICK

async def handle_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = user_data.get(update.effective_user.id, {})
    data['nick'] = update.message.text

    message = f"Новая заявка: Имя: {data.get('name')}, Телефон: {data.get('phone')}, Ник: {data.get('nick')}"
    await context.bot.send_message(chat_id=ADMIN_USERNAME, text=message)
    await update.message.reply_text("📬 Заявка отправлена организатору!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END

app = ApplicationBuilder().token("8174104659:AAGyXNs81m-pvaKXisKIdIaGGIV5rBj6uxQ").build()

app.add_handler(CommandHandler("start", start))

result_conv = ConversationHandler(
    entry_points=[CommandHandler("result", result_start)],
    states={
        PHOTO: [MessageHandler(filters.PHOTO, handle_photo)],
        RESULT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_result_text)],
        TOURNAMENT: [CallbackQueryHandler(handle_tournament)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)
app.add_handler(result_conv)

application_conv = ConversationHandler(
    entry_points=[CommandHandler("register", application_start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
        NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_nick)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)
app.add_handler(application_conv)

print("Бот запущен!")
app.run_polling()