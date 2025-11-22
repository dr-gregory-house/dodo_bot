import json
import os
from telegram import Update
from telegram.ext import ContextTypes

from datetime import datetime
from services.sheets import get_preps

GROUP_FILE = 'data/group.json'

async def set_group_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /set_group command.
    Saves the current chat ID as the group for notifications.
    """
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if chat_type not in ['group', 'supergroup']:
        await update.message.reply_text("Эту команду нужно использовать в группе пиццерии.")
        return

    try:
        data = {'group_id': str(chat_id)}
        
        os.makedirs('data', exist_ok=True)
        
        with open(GROUP_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        await update.message.reply_text(f"✅ Группа успешно привязана! ID: {chat_id}\nТеперь сюда будут приходить уведомления о заготовках.")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при сохранении группы: {e}")

async def prep_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /prep command.
    Shows preps for the next shift.
    """
    try:
        now = datetime.now()
        day_index = now.weekday()
        
        # Logic:
        # If time < 16:00 -> Show Evening Preps for Today (is_morning=False)
        # If time >= 16:00 -> Show Morning Preps for Tomorrow (is_morning=True, day+1)
        
        target_day_index = day_index
        is_morning = False
        
        if now.hour < 16:
            # Before 16:00: Show Evening preps (for the evening shift starting soon)
            is_morning = False
            shift_name = "на вечернюю смену"
        else:
            # After 16:00: Show Morning preps for tomorrow
            target_day_index = (day_index + 1) % 7
            is_morning = True
            shift_name = "на утреннюю смену завтра"
            
        await update.message.reply_text(f"⏳ Загружаю список заготовок {shift_name}...")
        
        preps_text = await get_preps(target_day_index, is_morning)
        
        await update.message.reply_text(preps_text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении заготовок: {e}")

async def who_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /who command.
    Shows who's working today.
    """
    try:
        now = datetime.now()
        today_str = now.strftime("%d.%m")
        
        await update.message.reply_text("⏳ Загружаю список сотрудников на смене...")
        
        from services.sheets import get_who_on_shift
        who_text = await get_who_on_shift(today_str)
        
        await update.message.reply_text(who_text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении списка: {e}")
