from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from services.sheets import get_all_employees
import json
import os

USERS_FILE = 'data/users.json'

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    os.makedirs('data', exist_ok=True)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    surname = users.get(str(user.id), 'Сотрудник')
    
    keyboard = [
        ["Разморозка", "Заготовки"],
        ["График", "Система оплаты труда"],
        ["Обеденный перерыв", "📊 Рейтинг"],
        ["🏥 Мед. комиссия", "📖 Инструкции для сотрудников"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # Inline keyboard with URL button
    inline_keyboard = [[InlineKeyboardButton("🤖 Codo-бот. Актуальная информация", url="https://t.me/dodo_codo_bot")]]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"👋 **Привет, {surname}!**\nЧем могу помочь сегодня? 🍕",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Send inline button separately
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="📲 **Дополнительно:**",
        reply_markup=inline_markup,
        parse_mode='Markdown'
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    
    # Check if user is already registered
    if str(user.id) in users:
        surname = users[str(user.id)]
        
        keyboard = [[InlineKeyboardButton("🔄 Это не я", callback_data="reset_user")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 Привет, {surname}! Вы авторизованы в системе.",
            reply_markup=reply_markup
        )
        await show_menu(update, context)
        return

    # Not registered, show employee list
    await update.message.reply_text("⏳ Загружаю список сотрудников...")
    
    employees = await get_all_employees()
    if not employees:
        await update.message.reply_text("⚠️ Не удалось загрузить список сотрудников. Попробуйте позже.")
        return
        
    # Build keyboard with employees
    keyboard = []
    row = []
    for emp in employees:
        # Callback data: "reg_<Name>"
        # Truncate if too long? Telegram has 64 bytes limit for callback_data.
        # Names are usually short enough.
        callback_data = f"reg_{emp}"
        # Ensure callback data is not too long
        if len(callback_data.encode('utf-8')) > 60:
             # Fallback or skip?
             pass
             
        row.append(InlineKeyboardButton(emp, callback_data=callback_data))
        if len(row) == 2: # 2 buttons per row
            keyboard.append(row)
            row = []
            
    if row:
        keyboard.append(row)
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👇 Пожалуйста, выберите вашу фамилию из списка:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = update.effective_user
    
    if data == "reset_user":
        # Remove user
        users = load_users()
        if str(user.id) in users:
            del users[str(user.id)]
            save_users(users)
            
        await query.edit_message_text("🔄 Регистрация сброшена.")
        
        # Trigger start logic again
        # We can't call start(update, context) directly easily because update is CallbackQuery here, not Message.
        # So we replicate the "Not registered" logic.
        
        await query.message.reply_text("⏳ Загружаю список сотрудников...")
        employees = await get_all_employees()
        
        keyboard = []
        row = []
        for emp in employees:
            callback_data = f"reg_{emp}"
            row.append(InlineKeyboardButton(emp, callback_data=callback_data))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "👇 Пожалуйста, выберите вашу фамилию из списка:",
            reply_markup=reply_markup
        )
        
    elif data.startswith("reg_"):
        selected_name = data[4:] # Remove "reg_"
        
        users = load_users()
        
        # Check if name is already taken by another user
        for chat_id, name in users.items():
            if name == selected_name and chat_id != str(user.id):
                await query.edit_message_text(
                    f"⚠️ **{selected_name}** уже зарегистрирован в системе.\n\n"
                    "Если это ваш аккаунт, попросите администратора сбросить предыдущую регистрацию.\n"
                    "Если это не вы, пожалуйста, выберите правильную фамилию.",
                    parse_mode='Markdown'
                )
                return
        
        users[str(user.id)] = selected_name
        save_users(users)
        
        await query.edit_message_text(f"✅ Вы успешно зарегистрированы как {selected_name}.")
        await show_menu(update, context)

# Export handlers
start_handler = CommandHandler('start', start)
registration_handler = CallbackQueryHandler(button_handler, pattern="^(reset_user|reg_.*)$")
