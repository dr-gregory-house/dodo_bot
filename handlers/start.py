from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

SURNAME = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍕 **Привет! Я бот Додо Пиццы!** 🧡\n\n"
        "Я помогу тебе с графиком, заготовками и другой полезной информацией.\n"
        "👇 **Пожалуйста, введи свою фамилию, чтобы начать:**",
        parse_mode='Markdown'
    )
    return SURNAME

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    surname = context.user_data.get('surname', 'Сотрудник')
    
    keyboard = [
        ["Разморозка", "Заготовки"],
        ["График", "Система оплаты труда"],
        ["Обеденный перерыв", "📊 Рейтинг"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # Inline keyboard with URL button
    inline_keyboard = [[InlineKeyboardButton("🤖 Codo-бот. Актуальная информация", url="https://t.me/dodo_codo_bot")]]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    await update.message.reply_text(
        f"👋 **Привет, {surname}!**\nЧем могу помочь сегодня? 🍕",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Send inline button separately
    await update.message.reply_text(
        "📲 **Дополнительно:**",
        reply_markup=inline_markup,
        parse_mode='Markdown'
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
