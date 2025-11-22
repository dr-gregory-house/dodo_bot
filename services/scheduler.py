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

        now = datetime.now()
        day_index = now.weekday() # 0=Mon, 6=Sun
        
        # Determine if it's morning or evening based on current time
        # We expect this function to be called around 8:55 or 16:55
        # Let's use a 30 min window to decide
        
        is_morning = False
        if 8 <= now.hour < 12:
            is_morning = True
        elif 16 <= now.hour < 20:
            is_morning = False
        else:
            # Fallback or maybe we shouldn't run?
            # If we run at 8:55, it's morning.
            # If we run at 16:55, it's evening.
            pass
            
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

        now = datetime.now()
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
    Check shifts for today and notify users 1 hour before start.
    """
    try:
        now = datetime.now()
        today_str = now.strftime("%d.%m")
        
        # Load data
        users = load_json(USERS_FILE)
        notifications = load_json(NOTIFICATIONS_FILE)
        
        if not users:
            return

        # Get shifts for today
        shifts = await get_shifts_for_date(today_str)
        if not shifts:
            return

        for shift_data in shifts:
            name = shift_data['name']
            shift_time = shift_data['shift']
            
            # Find user_id for this name
            user_id = None
            for uid, surname in users.items():
                if surname.lower() in name.lower():
                    user_id = uid
                    break
            
            if not user_id:
                continue
                
            # Check if already notified today
            last_notified = notifications.get(user_id)
            if last_notified == today_str:
                continue
                
            # Parse start time
            start_h, start_m = parse_start_time(shift_time)
            if start_h is None:
                continue
                
            # Construct shift start datetime
            shift_start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
            
            # Handle case where shift start is tomorrow (unlikely for "today's shift" but possible if parsed wrong)
            # Actually, get_shifts_for_date returns shifts for the date we asked.
            # So shift_start is on 'now' date.
            
            # Calculate time difference
            # If shift is 9:00 and now is 8:00, diff is 1 hour.
            # We want to notify if 0 < (shift_start - now) <= 1 hour + buffer?
            # Requirement: "1 hour before shift"
            
            time_until_shift = shift_start - now
            minutes_until = time_until_shift.total_seconds() / 60
            
            # Notify if within 60 minutes (and not passed more than 15 mins ago? No, strictly before)
            # Let's say we check every 5 mins.
            # We want to catch it when it's between 55 and 65 minutes?
            # Or just "less than 60 mins and not notified".
            # But if we restart bot at 8:30 for 9:00 shift, we should notify.
            # So: if 0 < minutes_until <= 65 (give 5 min buffer for the cron job)
            
            if 0 < minutes_until <= 65:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="Пора собираться на работу, опаздывать не красиво!"
                    )
                    logger.info(f"Sent notification to {name} ({user_id}) for shift {shift_time}")
                    
                    # Mark as notified
                    notifications[user_id] = today_str
                    save_json(NOTIFICATIONS_FILE, notifications)
                    
                except Exception as e:
                    logger.error(f"Failed to send notification to {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in check_shifts_and_notify: {e}")
