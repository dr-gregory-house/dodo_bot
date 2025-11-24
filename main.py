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

    from handlers.start import start_handler, registration_handler
    from handlers.menu import menu_message_handler
    from handlers.preps import preps_handler
    from handlers.defrost import defrost_handler
    from handlers.wages import wages_message_handler
    from handlers.lunch import lunch_message_handler
    from handlers.ratings import ratings_message_handler, upload_rs_handler, upload_rp_handler
    from handlers.schedule import schedule_callback_handler
    from handlers.group_setup import set_group_handler, prep_command_handler, who_command_handler
    from handlers.medical import medical_handlers

    application.add_handler(start_handler)
    application.add_handler(registration_handler)
    application.add_handler(preps_handler)
    application.add_handler(defrost_handler)
    application.add_handler(wages_message_handler)
    application.add_handler(lunch_message_handler)
    for handler in medical_handlers:
        application.add_handler(handler)
    application.add_handler(ratings_message_handler)
    application.add_handler(upload_rs_handler)
    application.add_handler(upload_rp_handler)
    application.add_handler(schedule_callback_handler)
    application.add_handler(menu_message_handler)
    
    # Command to set group for notifications
    application.add_handler(CommandHandler("set_group", set_group_handler))
    
    # Command to manually check preps
    application.add_handler(CommandHandler("prep", prep_command_handler))
    
    # Command to check who's working today
    application.add_handler(CommandHandler("who", who_command_handler))

    print("Bot is running...")
    
    # Add scheduler job
    if application.job_queue:
        from services.scheduler import check_shifts_and_notify, send_preps_notification, send_who_notification, send_feedback_notification
        from datetime import time
        import pytz
        
        # Run every 5 minutes (300 seconds)
        application.job_queue.run_repeating(check_shifts_and_notify, interval=300, first=10)
        
        # Schedule preps notifications (Moscow time)
        # 8:55 and 16:55
        tz = pytz.timezone('Europe/Moscow')
        application.job_queue.run_daily(send_preps_notification, time(8, 55, tzinfo=tz))
        application.job_queue.run_daily(send_preps_notification, time(16, 55, tzinfo=tz))
        
        # Schedule who's working notification at 8:00
        application.job_queue.run_daily(send_who_notification, time(8, 0, tzinfo=tz))

        # Schedule feedback notification at 22:50 (10:45 PM)
        application.job_queue.run_daily(send_feedback_notification, time(22, 52, tzinfo=tz))
        
        print("Scheduler started.")
    else:
        print("Warning: JobQueue not available. Notifications will not work.")

    application.run_polling()
