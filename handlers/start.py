from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

SURNAME = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот Додо Пиццы. Пожалуйста, введи свою фамилию, чтобы я мог найти твой график."
    )
    return SURNAME

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    surname = context.user_data.get('surname', 'Сотрудник')
    
    keyboard = [
        ["Разморозка", "Заготовки"],
        ["График", "Система оплаты труда"],
        ["Обеденный перерыв"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Что ты хочешь сделать, {surname}?",
        reply_markup=reply_markup
    )

async def save_surname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    surname = update.message.text
    context.user_data['surname'] = surname
    await show_menu(update, context)
    return ConversationHandler.END

start_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_surname)]
    },
    fallbacks=[]
)
