import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from config import BOT_TOKEN
from handlers.start import start_handler
from handlers.menu import menu_message_handler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in .env")
        # exit(1) # Commented out for testing without token if needed, but usually required.

    application = ApplicationBuilder().token(BOT_TOKEN or "TOKEN").build()

    from handlers.start import start_handler
    from handlers.menu import menu_message_handler
    from handlers.preps import preps_handler
    from handlers.defrost import defrost_handler
    from handlers.wages import wages_message_handler
    from handlers.lunch import lunch_message_handler
    from handlers.ratings import ratings_message_handler, upload_rs_handler, upload_rp_handler
    from handlers.schedule import schedule_callback_handler

    application.add_handler(start_handler)
    application.add_handler(preps_handler)
    application.add_handler(defrost_handler)
    application.add_handler(wages_message_handler)
    application.add_handler(lunch_message_handler)
    application.add_handler(ratings_message_handler)
    application.add_handler(upload_rs_handler)
    application.add_handler(upload_rp_handler)
    application.add_handler(schedule_callback_handler)
    application.add_handler(menu_message_handler)

    print("Bot is running...")
    application.run_polling()
