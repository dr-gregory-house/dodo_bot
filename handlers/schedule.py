from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from services.sheets import get_schedule, get_who_on_shift
from datetime import datetime

async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    surname = context.user_data.get('surname')
    if not surname:
        await update.message.reply_text("Сначала введи фамилию через /start")
        return

    schedule_text = await get_schedule(surname)
    
    # Create inline keyboard with two buttons
    inline_keyboard = [
        [InlineKeyboardButton("👥 Кто на смене", callback_data="who_on_shift")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    
    await update.message.reply_text(
        f"\n{schedule_text}",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "who_on_shift":
        # Get today's date in DD.MM format
        today = datetime.now().strftime("%d.%m")
        surname = context.user_data.get('surname')
        
        shift_info = await get_who_on_shift(today, surname)
        
        # Edit message to show shift info
        await query.edit_message_text(
            text=shift_info
        )
    elif query.data == "main_menu":
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
schedule_callback_handler = CallbackQueryHandler(button_callback, pattern="^(who_on_shift|main_menu)$")
