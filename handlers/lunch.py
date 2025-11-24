from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

async def lunch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🍽 **Информация по обеденному перерыву**\n\n"
        "**Правила перерывов:**\n"
        "• Смена 4 часа: перерыв 15 минут (1 закуска - 70₽)\n"
        "• Смена 8 часов: перерыв 30 минут (2 закуски - 140₽)\n"
        "• Смена 11-14 часов: перерыв 1 час (3 закуски - 210₽)\n\n"
        "👥 **На обед могут ходить вместе:**\n"
        "• 1 пиццамейкер + 1 кассир\n"
        "• 1 пиццамейкер + менеджер"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

lunch_message_handler = MessageHandler(filters.Regex("^Обеденный перерыв$"), lunch_handler)
