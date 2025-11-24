from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

DEFROST_DAY_SELECT = 0

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

async def start_defrost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "❄️ **Правила разморозки**\n\n"
        "1. Доставать продукты нужно строго по списку.\n"
        "2. Клеить маркировку с датой и временем.\n\n"
        "⚠️ **ВАЖНО:**\n"
        "Разморозку **не складываем друг на друга**! Оставляйте место для циркуляции холодного воздуха и лексана разморозки.\n\n"
        "👇 **Выберите день недели для просмотра списка:**"
    )
    
    keyboard = [
        ["Понедельник", "Вторник", "Среда"],
        ["Четверг", "Пятница", "Суббота"],
        ["Воскресенье", "Назад"]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return DEFROST_DAY_SELECT

async def select_defrost_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Abort if a command is received while we expect a day name.
    if update.message.text.startswith('/'):
        return ConversationHandler.END
    text = update.message.text
    
    if text == "Назад":
        from handlers.start import show_menu
        await show_menu(update, context)
        return ConversationHandler.END
        
    if text not in DAYS:
        await update.message.reply_text("Пожалуйста, выберите день из меню.")
        return DEFROST_DAY_SELECT
        
    # Placeholder for actual data since we don't have a sheet for this yet
    day_info = f"📋 **Список разморозки на {text}:**\n\n(Список пока пуст. Попросите менеджера добавить данные.)"
    
    from handlers.start import show_menu
    await update.message.reply_text(day_info, parse_mode='Markdown')
    await show_menu(update, context)
    return ConversationHandler.END

defrost_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^Разморозка$"), start_defrost)],
    states={
        DEFROST_DAY_SELECT: [MessageHandler(filters.TEXT, select_defrost_day)]
    },
    fallbacks=[]
)
