import json
import os
import csv
import httpx
import io
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

RATINGS_FILE = "data/ratings.json"
PHOTO_UPLOAD = 0
SCHEDULE_URL = "https://docs.google.com/spreadsheets/d/1hbvUroW0SxAbTbsn0nn-9wJyYKz-zLDJQ_PS7b83SzA/export?format=csv&gid=1833845756"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

def load_ratings():
    if not os.path.exists(RATINGS_FILE):
        return {"rs": None, "rp": None}
    with open(RATINGS_FILE, "r") as f:
        return json.load(f)

def save_ratings(data):
    with open(RATINGS_FILE, "w") as f:
        json.dump(data, f)

async def get_ratings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_ratings()
    
    if not data["rs"] and not data["rp"]:
        await update.message.reply_text("📉 **Рейтинги пока не загружены.**\nПопросите менеджера обновить данные.", parse_mode='Markdown')
        return

    if data["rs"]:
        await update.message.reply_photo(photo=data["rs"], caption="📉 **Рейтинг Стандартов (РС)**", parse_mode='Markdown')
    
    if data["rp"]:
        await update.message.reply_photo(photo=data["rp"], caption="🤩 **Рейтинг Продукта (РП)**", parse_mode='Markdown')

# --- Upload Handlers ---

async def check_authorization(context: ContextTypes.DEFAULT_TYPE):
    """Check if user is authorized to upload ratings. Returns (is_authorized, role)"""
    surname = context.user_data.get('surname', '').lower()
    
    # Hardcoded authorized managers
    if 'мишра' in surname:
        return True, "Мишра"
    elif 'ахмитенко' in surname:
        return True, "Менеджер"
    
    return False, None

async def start_upload_rs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 **Проверка прав доступа...**", parse_mode='Markdown')
    
    is_authorized, role = await check_authorization(context)
    
    if not is_authorized:
        await update.message.reply_text(
            "❌ **Доступ запрещён.**\nТолько менеджеры могут обновлять рейтинги.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"✅ **Доступ разрешён!** Вы - {role}.\n\n📸 Отправьте фото для Рейтинга Стандартов (РС):",
        parse_mode='Markdown'
    )
    context.user_data['upload_type'] = 'rs'
    return PHOTO_UPLOAD

async def start_upload_rp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 **Проверка прав доступа...**", parse_mode='Markdown')
    
    is_authorized, role = await check_authorization(context)
    
    if not is_authorized:
        await update.message.reply_text(
            "❌ **Доступ запрещён.**\nТолько менеджеры могут обновлять рейтинги.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"✅ **Доступ разрешён!** Вы - {role}.\n\n📸 Отправьте фото для Рейтинга Продукта (РП):",
        parse_mode='Markdown'
    )
    context.user_data['upload_type'] = 'rp'
    return PHOTO_UPLOAD

async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = update.message.photo[-1].file_id
    upload_type = context.user_data.get('upload_type')
    
    data = load_ratings()
    data[upload_type] = photo_file
    save_ratings(data)
    
    name = "РС" if upload_type == 'rs' else "РП"
    await update.message.reply_text(f"✅ **Фото для {name} успешно обновлено!**", parse_mode='Markdown')
    return ConversationHandler.END

async def cancel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Обновление отменено.")
    return ConversationHandler.END

ratings_message_handler = MessageHandler(filters.Regex("^📊 Рейтинг$"), get_ratings)

upload_rs_handler = ConversationHandler(
    entry_points=[CommandHandler('set_rs', start_upload_rs)],
    states={
        PHOTO_UPLOAD: [MessageHandler(filters.PHOTO, save_photo)]
    },
    fallbacks=[CommandHandler('cancel', cancel_upload)]
)

upload_rp_handler = ConversationHandler(
    entry_points=[CommandHandler('set_rp', start_upload_rp)],
    states={
        PHOTO_UPLOAD: [MessageHandler(filters.PHOTO, save_photo)]
    },
    fallbacks=[CommandHandler('cancel', cancel_upload)]
)
