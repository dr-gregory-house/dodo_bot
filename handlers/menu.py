from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from handlers.schedule import schedule_handler

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "График":
        await schedule_handler(update, context)
    elif text == "Главное меню" or text == "Назад":
        from handlers.start import show_menu
        await show_menu(update, context)
    # Разморозка and Заготовки are handled by their respective ConversationHandlers
    # Wages is now handled by its own handler
    else:
        await update.message.reply_text("Неизвестная команда.")

menu_message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)
