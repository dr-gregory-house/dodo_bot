from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from services.sheets import get_preps

DAY_SELECT, TIME_SELECT = range(2)

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

async def start_preps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Понедельник", "Вторник", "Среда"],
        ["Четверг", "Пятница", "Суббота"],
        ["Воскресенье", "Главное меню"]
    ]
    await update.message.reply_text(
        "👇 **Выберите день недели:**",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return DAY_SELECT

async def select_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Abort if a command is received while we expect a day name.
    if update.message.text.startswith('/'):
        return ConversationHandler.END
    text = update.message.text
    if text == "Главное меню" or text == "Назад":
        from handlers.start import show_menu
        await show_menu(update, context)
        return ConversationHandler.END
        
    if text not in DAYS:
        await update.message.reply_text("Пожалуйста, выберите день из меню.")
        return DAY_SELECT
        
    context.user_data['prep_day'] = DAYS.index(text)
    
    keyboard = [["Утро", "Вечер"], ["Назад"]]
    await update.message.reply_text(
        f"Выбран {text}. Какая смена?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return TIME_SELECT

async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Abort if a command is received while we expect a time selection.
    if update.message.text.startswith('/'):
        return ConversationHandler.END
    text = update.message.text
    if text == "Назад":
        return await start_preps(update, context)
        
    if text not in ["Утро", "Вечер"]:
        await update.message.reply_text("Выберите Утро или Вечер.")
        return TIME_SELECT
        
    is_morning = (text == "Утро")
    day_index = context.user_data['prep_day']
    
    await update.message.reply_text("Загружаю данные...")
    result = await get_preps(day_index, is_morning)
    
    # Loop back to day selection instead of main menu
    await update.message.reply_text(result, parse_mode='Markdown')
    return await start_preps(update, context)

preps_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^Заготовки$"), start_preps)],
    states={
        DAY_SELECT: [MessageHandler(filters.TEXT, select_day)],
        TIME_SELECT: [MessageHandler(filters.TEXT, select_time)]
    },
    fallbacks=[]
)
