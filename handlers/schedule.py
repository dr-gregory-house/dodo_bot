from telegram import Update
from telegram.ext import ContextTypes
from services.sheets import get_schedule

async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    surname = context.user_data.get('surname')
    if not surname:
        await update.message.reply_text("Сначала введи фамилию через /start")
        return

    schedule_text = await get_schedule(surname)
    await update.message.reply_text(f"Твой график:\n{schedule_text}")
