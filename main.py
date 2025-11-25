import logging
import logging.handlers
import signal
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ApplicationHandlerStop
from config import BOT_TOKEN
from handlers.start import start_handler
from handlers.menu import menu_message_handler
from services.auth import is_user_admin, get_user_role

async def group_restriction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Restrict usage in groups to Admins and Managers only.
    """
    if update.effective_chat.type in ['group', 'supergroup']:
        user_id = update.effective_user.id
        
        # 1. Check if Telegram Admin
        if await is_user_admin(update, context):
            return # Authorized
            
        # 2. Check if Manager (by surname)
        role = await get_user_role(user_id, context)
        if role:
            return # Authorized
            
        # Not authorized - Stop processing
        raise ApplicationHandlerStop

# Production logging setup with file rotation
import os
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console handler for stdout
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler with rotation (10MB per file, keep 5 backups)
file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(log_dir, 'dodo_bot.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Error file handler for errors only
error_handler = logging.handlers.RotatingFileHandler(
    os.path.join(log_dir, 'dodo_bot_errors.log'),
    maxBytes=10*1024*1024,
    backupCount=5,
    encoding='utf-8'
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(file_formatter)
logger.addHandler(error_handler)

# Graceful shutdown handler
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    logger.info("Starting Dodo Bot...")
    
    if not BOT_TOKEN:
        logger.error("Error: BOT_TOKEN not found in .env file")
        sys.exit(1)

    try:
        application = ApplicationBuilder().token(BOT_TOKEN).build()
    except Exception as e:
        logger.error(f"Failed to initialize bot application: {e}")
        sys.exit(1)

    from handlers.start import start_handler, registration_handler
    from handlers.menu import menu_message_handler
    from handlers.preps import preps_handler
    from handlers.defrost import defrost_handler
    from handlers.wages import wages_message_handler
    from handlers.lunch import lunch_message_handler
    from handlers.ratings import ratings_message_handler, upload_rs_handler, upload_rp_handler, rs_command_handler, rp_command_handler
    from handlers.schedule import schedule_callback_handler
    from handlers.group_setup import set_group_handler, prep_command_handler, who_command_handler
    from handlers.medical import medical_handlers
    from handlers.message_handler import text_collection_handler, photo_collection_handler
    from handlers.worker_instructions import worker_instructions_message_handler, instructions_callback

    # Restriction Handler (Group -1)
    # Restrict all commands in groups to Admins/Managers
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.COMMAND, group_restriction_handler), group=-1)

    application.add_handler(start_handler)
    application.add_handler(registration_handler)
    application.add_handler(preps_handler)
    application.add_handler(defrost_handler)
    application.add_handler(wages_message_handler)
    application.add_handler(lunch_message_handler)
    application.add_handler(worker_instructions_message_handler)
    application.add_handler(instructions_callback)
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
    
    # Commands to show ratings in group
    application.add_handler(rs_command_handler)
    application.add_handler(rp_command_handler)
    
    # Message collection handlers (add at lower priority so other handlers process first)
    application.add_handler(text_collection_handler, group=10)
    application.add_handler(photo_collection_handler, group=10)

    logger.info("Bot handlers registered successfully")
    
    # Add scheduler job
    if application.job_queue:
        from services.scheduler import check_shifts_and_notify, send_preps_notification, send_who_notification, send_feedback_notification, reset_daily_data_job
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

        # Schedule feedback notification at 22:50 (10:50 PM)
        application.job_queue.run_daily(send_feedback_notification, time(22, 50, tzinfo=tz))
        
        # Schedule daily data cleanup at midnight
        application.job_queue.run_daily(reset_daily_data_job, time(0, 0, tzinfo=tz))
        
        logger.info("Scheduler started - all jobs registered")
    else:
        logger.warning("JobQueue not available. Notifications will not work.")

    logger.info("Starting polling... Bot is now running in production mode")
    try:
        application.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}", exc_info=True)
        sys.exit(1)
