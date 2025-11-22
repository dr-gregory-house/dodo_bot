from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from services.sheets import get_schedule, get_who_on_shift
from datetime import datetime, timedelta

async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    surname = context.user_data.get('surname')
    if not surname:
        await update.message.reply_text("Сначала введи фамилию через /start")
        return

    await show_schedule(update, context, surname, offset=0, is_new=True)

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE, surname: str, offset: int = 0, is_new: bool = False):
    """
    Helper to show schedule with pagination.
    offset: 0 means current week (closest to today).
            +1 means next week relative to current.
            -1 means prev week relative to current.
    """
    schedules = await get_schedule(surname)
    
    if not schedules:
        msg = f"Сотрудник с фамилией '{surname}' не найден в графике или смен нет."
        if is_new:
            await update.message.reply_text(msg)
        else:
            await update.callback_query.edit_message_text(msg)
        return

    # Find the "current" week index
    # We want the week that contains today, or the first future week if today is past all.
    # Actually, let's just find the week closest to today.
    
    now = datetime.now()
    current_index = 0
    min_diff = float('inf')
    
    # Simple logic: find the week where start_date <= now <= end_date?
    # Or just start_date is closest to now - 3 days (to handle end of week).
    # Let's pick the week that started most recently but not too far in future?
    
    # Better: Find the index where start_date is closest to (now - weekday).
    # Monday of this week.
    monday_of_current_week = now - timedelta(days=now.weekday())
    monday_of_current_week = monday_of_current_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Find index with start_date closest to monday_of_current_week
    for i, sched in enumerate(schedules):
        diff = abs((sched['start_date'] - monday_of_current_week).days)
        if diff < min_diff:
            min_diff = diff
            current_index = i
            
    # Apply offset
    target_index = current_index + offset
    
    # Clamp index
    if target_index < 0: target_index = 0
    if target_index >= len(schedules): target_index = len(schedules) - 1
    
    schedule = schedules[target_index]
    
    # Buttons
    buttons = []
    nav_row = []
    
    if target_index > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Пред. неделя", callback_data=f"sched_offset:{offset-1}"))
    
    if target_index < len(schedules) - 1:
        nav_row.append(InlineKeyboardButton("След. неделя ➡️", callback_data=f"sched_offset:{offset+1}"))
        
    if nav_row:
        buttons.append(nav_row)
        
    buttons.append([InlineKeyboardButton("👥 Кто на смене", callback_data="who_on_shift")])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    text = schedule['text']
    
    if is_new:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        # Check if text changed to avoid errors
        try:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        except:
            pass

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("sched_offset:"):
        offset = int(data.split(":")[1])
        surname = context.user_data.get('surname')
        
        if not surname:
            await query.answer("⚠️ Сессия истекла. Введи фамилию заново через /start", show_alert=True)
            try:
                await query.edit_message_text("⚠️ Сессия истекла. Пожалуйста, введите фамилию заново через /start")
            except:
                pass
            return

        await show_schedule(update, context, surname, offset=offset, is_new=False)
        
    elif data == "who_on_shift":
        # Get today's date in DD.MM format
        today = datetime.now().strftime("%d.%m")
        surname = context.user_data.get('surname')
        
        shift_info = await get_who_on_shift(today, surname)
        
        # Add back button to schedule? Or just main menu.
        # Let's keep it simple.
        keyboard = [[InlineKeyboardButton("🔙 К графику", callback_data="sched_offset:0")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=shift_info,
            reply_markup=reply_markup
        )
    elif data == "main_menu":
        # Return to main menu
        surname = context.user_data.get('surname', 'Сотрудник')
        
        keyboard = [
            ["Разморозка", "Заготовки"],
            ["График", "Система оплаты труда"],
            ["Обеденный перерыв", "📊 Рейтинг"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await query.edit_message_text(
            text=f"👋 **Привет, {surname}!**\nВыбери действие из меню 👇",
            parse_mode='Markdown'
        )
        # Send a new message with the keyboard since we can't add ReplyKeyboardMarkup to edited messages
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🏠 Главное меню:",
            reply_markup=reply_markup
        )

# Create the callback query handler
schedule_callback_handler = CallbackQueryHandler(button_callback, pattern="^(who_on_shift|main_menu|sched_offset:.*)$")
