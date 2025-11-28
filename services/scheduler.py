import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from services.sheets import get_shifts_for_date, get_preps

logger = logging.getLogger(__name__)

USERS_FILE = 'data/users.json'
NOTIFICATIONS_FILE = 'data/notifications.json'
GROUP_FILE = 'data/group.json'

def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return {}

def save_json(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")

def parse_start_time(shift_str):
    """
    Parse start time from shift string like '9-17' or '09:00-17:00'.
    Returns hour (int) and minute (int).
    """
    try:
        # Remove spaces
        shift_str = shift_str.replace(' ', '')
        # Split by '-'
        parts = shift_str.split('-')
        if not parts:
            return None, None
            
        start_str = parts[0]
        
        if ':' in start_str:
            h, m = map(int, start_str.split(':'))
            return h, m
        else:
            # Assume just hour if no colon
            return int(start_str), 0
    except:
        return None, None

async def send_preps_notification(context: ContextTypes.DEFAULT_TYPE):
    """
    Send preps notification to the group.
    Scheduled to run at specific times (Morning and Evening).
    """
    try:
        # Load group ID
        group_data = load_json(GROUP_FILE)
        group_id = group_data.get('group_id')
        
        if not group_id:
            return

        import pytz
        tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(tz)
        day_index = now.weekday() # 0=Mon, 6=Sun
        
        # Determine if it's morning or evening based on current time
        # Scheduled times: 8:55 MSK (Morning) and 16:55 MSK (Evening)
        
        # Explicitly convert to MSK to be sure, but also check UTC hour as fallback
        # 8:55 MSK is 5:55 UTC
        # 16:55 MSK is 13:55 UTC
        
        now_utc = datetime.now(pytz.utc)
        now_msk = now_utc.astimezone(tz)
        
        hour_msk = now_msk.hour
        hour_utc = now_utc.hour
        
        logger.info(f"Preps Notification Triggered. Time: {now_msk} (MSK), Hour: {hour_msk}. UTC Hour: {hour_utc}")
        
        is_morning = False
        
        # Morning check: 8 AM MSK or 5 AM UTC
        if hour_msk == 8 or hour_utc == 5:
            is_morning = True
            
        # Evening check: 16 PM MSK or 13 PM UTC
        elif hour_msk == 16 or hour_utc == 13:
            is_morning = False
            
        else:
            # Fallback for manual runs or weird timing
            if 4 <= hour_utc < 10: # Morning window
                is_morning = True
            else:
                is_morning = False
            logger.warning(f"Unexpected execution time. Defaulting to Morning={is_morning}")
            
        # Fetch preps
        preps_text = await get_preps(day_index, is_morning)
        
        # Add header
        header = "🔔 **Напоминание о заготовках**\n\n"
        message = header + preps_text
        
        await context.bot.send_message(
            chat_id=group_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info(f"Sent preps notification to group {group_id} (Morning={is_morning})")
        
    except Exception as e:
        logger.error(f"Error sending preps notification: {e}")

async def send_who_notification(context: ContextTypes.DEFAULT_TYPE):
    """
    Send "who's working today" notification to the group.
    Scheduled to run daily at 8:00.
    """
    try:
        # Load group ID
        group_data = load_json(GROUP_FILE)
        group_id = group_data.get('group_id')
        
        if not group_id:
            return

        import pytz
        tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(tz)
        today_str = now.strftime("%d.%m")
        
        # Fetch who's on shift
        from services.sheets import get_who_on_shift
        who_text = await get_who_on_shift(today_str)
        
        # Add header
        header = "🔔 **Кто сегодня работает**\n\n"
        message = header + who_text
        
        await context.bot.send_message(
            chat_id=group_id,
            text=message
        )
        logger.info(f"Sent who's working notification to group {group_id}")
        
    except Exception as e:
        logger.error(f"Error sending who's working notification: {e}")

async def check_shifts_and_notify(context: ContextTypes.DEFAULT_TYPE):
    """
    Check shifts for today and tomorrow and notify users 1 hour before start.
    """
    try:
        import pytz
        tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(tz)
        
        # Check today and tomorrow to handle midnight shifts
        dates_to_check = [now, now + timedelta(days=1)]
        
        # Load data
        users = load_json(USERS_FILE)
        notifications = load_json(NOTIFICATIONS_FILE)
        
        if not users:
            return

        for date_obj in dates_to_check:
            date_str = date_obj.strftime("%d.%m")
            
            # Get shifts for date
            shifts = await get_shifts_for_date(date_str)
            if not shifts:
                continue

            for shift_data in shifts:
                name = shift_data['name']
                shift_time = shift_data['shift']
                
                # Find ALL user_ids for this name (handle duplicates)
                matching_user_ids = []
                for uid, user_surname in users.items():
                    # Strict check: if user_surname is full name (new system) or surname (old system)
                    # New system: user_surname == "Ivanov Ivan" -> exact match or contained
                    # Old system: user_surname == "Ivanov" -> contained
                    
                    if user_surname.lower() in name.lower():
                        matching_user_ids.append(uid)
                
                if not matching_user_ids:
                    continue
                    
                for user_id in matching_user_ids:
                    # Check if already notified for this date
                    # We store "date_str" in notifications. 
                    # If a user has multiple shifts in a day (rare), this might skip the second one.
                    # But usually one shift per day.
                    last_notified = notifications.get(user_id)
                    if last_notified == date_str:
                        continue
                        
                    # Parse start time
                    start_h, start_m = parse_start_time(shift_time)
                    if start_h is None:
                        continue
                        
                    # Construct shift start datetime
                    # We need to be careful with the date. 
                    # shift_data comes from 'date_str' which corresponds to 'date_obj'
                    
                    shift_start = date_obj.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                    
                    # Handle case where parsed hour is < 24 but technically it might be next day?
                    # No, get_shifts_for_date returns shifts for that specific calendar date.
                    # So if date is 24.11 and shift is 00:00, it means 00:00 on 24.11.
                    # Wait, usually 00:00 shift is considered start of the day.
                    # If the schedule says "17-02", the 02 is next day.
                    # But parse_start_time only returns start time.
                    # If shift is "00-12", start is 00.
                    
                    # Calculate time difference
                    # We want to notify if we are roughly 1 hour before.
                    
                    time_until_shift = shift_start - now
                    minutes_until = time_until_shift.total_seconds() / 60
                    
                    # Notify if within 60 minutes (and not passed)
                    # Range: 0 < minutes <= 65
                    
                    if 0 < minutes_until <= 65:
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=f"⏰ Напоминание!\nТвоя смена начинается через час ({shift_time}).\nПора собираться на работу!"
                            )
                            logger.info(f"Sent notification to {name} ({user_id}) for shift {shift_time} on {date_str}")
                            
                            # Mark as notified for this date
                            notifications[user_id] = date_str
                            save_json(NOTIFICATIONS_FILE, notifications)
                            
                        except Exception as e:
                            logger.error(f"Failed to send notification to {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in check_shifts_and_notify: {e}")

async def send_feedback_notification(context: ContextTypes.DEFAULT_TYPE):
    """
    Analyze collected messages with LLM, then send feedback notification to the group.
    If LLM analysis fails, send raw collected messages as fallback.
    Scheduled to run daily at 22:52.
    """
    try:
        # First, analyze the day's messages with LLM
        from services.feedback_analyzer import analyze_feedback
        from services.message_collector import get_daily_data
        
        logger.info("Starting feedback analysis with LLM...")
        success = await analyze_feedback()
        
        # Load group ID
        group_data = load_json(GROUP_FILE)
        group_id = group_data.get('group_id')
        
        if not group_id:
            logger.warning("Group ID not found in group.json")
            return

        feedback_file = 'data/feedback.text'
        message = None
        
        # Try to read existing feedback.text file (from AI or manual)
        if os.path.exists(feedback_file):
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():  # Only use if not empty
                        message = content
                        logger.info("Using existing feedback.text file")
            except Exception as e:
                logger.error(f"Error reading feedback file: {e}")
        
        # If no existing feedback, create fallback message from raw data
        if not message:
            logger.warning("No existing feedback.text found, creating fallback message from raw data...")
            
            # Get collected messages
            messages = get_daily_data()
            
            if not messages:
                logger.info("No messages collected today and no feedback.text. Skipping feedback notification.")
                return
            
            # Create simple formatted message with raw data
            import pytz
            tz = pytz.timezone('Europe/Moscow')
            today = datetime.now(tz).strftime("%d.%m.%Y")
            
            message = f"📋 **Обратная связь за {today}**\n\n"
            message += "_⚠️ Автоматический анализ временно недоступен. Ниже сырые данные:_\n\n"
            
            text_count = 0
            image_count = 0
            
            for msg in messages:
                if msg.get('type') == 'image':
                    image_count += 1
                    user = f"{msg.get('first_name', '')} {msg.get('last_name', '')}".strip()
                    caption = msg.get('caption', '')
                    time = msg.get('timestamp', '')
                    message += f"📷 [{user}] {time}"
                    if caption:
                        message += f": {caption}"
                    message += "\n"
                elif msg.get('text'):
                    text_count += 1
                    user = f"{msg.get('first_name', '')} {msg.get('last_name', '')}".strip()
                    text = msg.get('text', '')
                    time = msg.get('timestamp', '')
                    message += f"💬 [{user}] {time}: {text}\n"
            
            message += f"\n📊 Всего: {text_count} текст. сообщ., {image_count} изображ."
        
        if not message.strip():
            logger.warning("No feedback content to send")
            return
        
        await context.bot.send_message(
            chat_id=group_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info(f"Sent feedback notification to group {group_id}")
        
    except Exception as e:
        logger.error(f"Error sending feedback notification: {e}")

async def reset_daily_data_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Job to clean up old message files.
    Scheduled to run daily at midnight.
    """
    try:
        from services.message_collector import reset_daily_data
        reset_daily_data()
        logger.info("Daily data reset completed")
    except Exception as e:
        logger.error(f"Error in reset_daily_data_job: {e}")
