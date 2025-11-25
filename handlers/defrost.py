from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import json
import os

DEFROST_MENU_SELECT, DEFROST_DAY_SELECT = range(2)

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

def load_json(filename):
    """Load JSON data from file."""
    filepath = os.path.join('data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

async def start_defrost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the three sub-menu options for defrosting."""
    keyboard = [
        ["Что должно быть в морозилке на 1 этаже"],
        ["Разморозка на 1 этаже"],
        ["Разморозка на 4 этаже"],
        ["🏠 Главное меню"]
    ]
    
    await update.message.reply_text(
        "❄️ **Разморозка**\n\nВыберите раздел:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return DEFROST_MENU_SELECT

async def select_defrost_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu selection."""
    # Abort if a command is received
    if update.message.text.startswith('/'):
        return ConversationHandler.END
    
    text = update.message.text
    
    if text == "🏠 Главное меню" or text == "Назад":
        from handlers.start import show_menu
        await show_menu(update, context)
        return ConversationHandler.END
    
    if text == "Что должно быть в морозилке на 1 этаже":
        # Load and display freezer inventory
        data = load_json('freezer_1st_floor.json')
        
        if not data:
            await update.message.reply_text("⚠️ Не удалось загрузить данные.")
            return DEFROST_MENU_SELECT
        
        # Format the message
        message = f"📦 **{data.get('title', 'Морозилка 1 этаж')}**\n"
        if 'description' in data:
            message += f"_{data['description']}_\n"
        message += "\n"
        
        for item in data.get('items', []):
            name = item.get('name', '')
            qty = item.get('quantity', '')
            message += f"🔹 {name} - {qty}\n"
        
        # Add instructions
        message += "\n⚠️ **Важно:**\n"
        message += "_Заполняем морозилку на 1 этаже после 19:00._\n"
        message += "_В морозилке на 1 этаже должно быть данное количество продуктов, все раскладываем аккуратно и не открываем по 2 коробки._"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        return DEFROST_MENU_SELECT
    
    elif text == "Разморозка на 4 этаже":
        # Load and display 4th floor defrosting
        data = load_json('defrost_4th_floor.json')
        
        if not data:
            await update.message.reply_text("⚠️ Не удалось загрузить данные.")
            return DEFROST_MENU_SELECT
        
        # Format the message
        message = f"❄️ **{data.get('title', 'Разморозка 4 этаж')}**\n\n"
        
        for item in data.get('items', []):
            name = item.get('name', '')
            qty = item.get('quantity', '')
            message += f"🔹 {name} - {qty}\n"
        
        # Add instructions
        message += "\n⚠️ **Важно:**\n"
        message += "_Разморозка на 4 этаже достается на колеса и закатывается в холодильник, не забываем наклеивать маркировки на коробки!_"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        return DEFROST_MENU_SELECT
    
    elif text == "Разморозка на 1 этаже":
        # Show day selection for 1st floor defrosting
        keyboard = [
            ["Понедельник", "Вторник", "Среда"],
            ["Четверг", "Пятница", "Суббота"],
            ["Воскресенье", "Назад"]
        ]
        await update.message.reply_text(
            "📅 **Выберите день недели:**",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode='Markdown'
        )
        return DEFROST_DAY_SELECT
    
    else:
        await update.message.reply_text("Пожалуйста, выберите раздел из меню.")
        return DEFROST_MENU_SELECT

async def select_defrost_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle day selection for 1st floor defrosting."""
    # Abort if a command is received
    if update.message.text.startswith('/'):
        return ConversationHandler.END
    
    text = update.message.text
    
    if text == "Назад":
        # Go back to main defrost menu
        return await start_defrost(update, context)
    
    if text not in DAYS:
        await update.message.reply_text("Пожалуйста, выберите день из меню.")
        return DEFROST_DAY_SELECT
    
    # Load 1st floor defrosting data
    data = load_json('defrost_1st_floor.json')
    
    if not data or 'days' not in data:
        await update.message.reply_text("⚠️ Не удалось загрузить данные.")
        return DEFROST_DAY_SELECT
    
    day_items = data['days'].get(text, [])
    
    if not day_items:
        await update.message.reply_text(f"⚠️ Нет данных для {text}.")
        return DEFROST_DAY_SELECT
    
    # Format the message
    message = f"❄️ **Разморозка на 1 этаже - {text}**\n\n"
    
    for item in day_items:
        name = item.get('name', '')
        qty = item.get('quantity', '')
        message += f"🔹 {name} - {qty}\n"
    
    # Add instructions
    message += "\n⚠️ **Важно:**\n"
    message += "_Разморозка на 1 этаже достается с утра, все раскладываем аккуратно и не друг на друга._\n"
    message += "_Не забываем наклеивать маркировки, все проверяем внимательно!_"
    
    await update.message.reply_text(message, parse_mode='Markdown')
    return DEFROST_DAY_SELECT

defrost_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^Разморозка$"), start_defrost)],
    states={
        DEFROST_MENU_SELECT: [MessageHandler(filters.TEXT, select_defrost_menu)],
        DEFROST_DAY_SELECT: [MessageHandler(filters.TEXT, select_defrost_day)]
    },
    fallbacks=[]
)
