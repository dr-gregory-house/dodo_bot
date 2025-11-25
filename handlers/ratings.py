import json
import os
import csv
import httpx
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters

RATINGS_FILE = "data/ratings.json"
PHOTO_UPLOAD_1 = 0
PHOTO_UPLOAD_2 = 1
SCHEDULE_URL = "https://docs.google.com/spreadsheets/d/1hbvUroW0SxAbTbsn0nn-9wJyYKz-zLDJQ_PS7b83SzA/export?format=csv&gid=1833845756"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

def load_ratings():
    if not os.path.exists(RATINGS_FILE):
        return {"rs": [], "rp": []}
    with open(RATINGS_FILE, "r") as f:
        data = json.load(f)
        # Ensure backward compatibility - convert old format to new
        if isinstance(data.get("rs"), str) or data.get("rs") is None:
            data["rs"] = [data["rs"]] if data.get("rs") else []
        if isinstance(data.get("rp"), str) or data.get("rp") is None:
            data["rp"] = [data["rp"]] if data.get("rp") else []
        return data

def save_ratings(data):
    with open(RATINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def get_ratings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_ratings()
    
    if not data["rs"] and not data["rp"]:
        await update.message.reply_text("📉 **Рейтинги пока не загружены.**\nПопросите менеджера обновить данные.", parse_mode='Markdown')
        return

    if data["rs"]:
        for idx, photo_id in enumerate(data["rs"], 1):
            if photo_id:
                await update.message.reply_photo(photo=photo_id, caption=f"📉 **Рейтинг Стандартов (РС) - Фото {idx}**", parse_mode='Markdown')
    
    if data["rp"]:
        for idx, photo_id in enumerate(data["rp"], 1):
            if photo_id:
                await update.message.reply_photo(photo=photo_id, caption=f"🤩 **Рейтинг Продукта (РП) - Фото {idx}**", parse_mode='Markdown')

# --- Upload Handlers ---

from services.auth import check_authorization

async def start_upload_rs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 **Проверка прав доступа...**", parse_mode='Markdown')
    
    is_authorized, role = await check_authorization(context, update.effective_user.id)
    
    if not is_authorized:
        await update.message.reply_text(
            "❌ **Доступ запрещён.**\nТолько менеджеры могут обновлять рейтинги.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"✅ **Доступ разрешён!** Вы - {role}.\n\n📸 Отправьте **первое фото** для Рейтинга Стандартов (РС):",
        parse_mode='Markdown'
    )
    context.user_data['upload_type'] = 'rs'
    context.user_data['photos'] = []
    return PHOTO_UPLOAD_1

async def start_upload_rp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 **Проверка прав доступа...**", parse_mode='Markdown')
    
    is_authorized, role = await check_authorization(context, update.effective_user.id)
    
    if not is_authorized:
        await update.message.reply_text(
            "❌ **Доступ запрещён.**\nТолько менеджеры могут обновлять рейтинги.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"✅ **Доступ разрешён!** Вы - {role}.\n\n📸 Отправьте **первое фото** для Рейтинга Продукта (РП):",
        parse_mode='Markdown'
    )
    context.user_data['upload_type'] = 'rp'
    context.user_data['photos'] = []
    return PHOTO_UPLOAD_1

async def save_first_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = update.message.photo[-1].file_id
    context.user_data['photos'].append(photo_file)
    
    upload_type = context.user_data.get('upload_type')
    name = "РС" if upload_type == 'rs' else "РП"
    
    # Offer choice: add second photo or finish
    keyboard = [
        [InlineKeyboardButton("📸 Добавить второе фото", callback_data=f"add_second_{upload_type}")],
        [InlineKeyboardButton("✅ Готово (сохранить 1 фото)", callback_data=f"finish_{upload_type}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ **Первое фото получено!**\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return PHOTO_UPLOAD_2

async def handle_photo_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    upload_type = context.user_data.get('upload_type')
    
    if data.startswith('add_second_'):
        name = "РС" if upload_type == 'rs' else "РП"
        await query.edit_message_text(
            f"📸 Отправьте **второе фото** для {name}:",
            parse_mode='Markdown'
        )
        return PHOTO_UPLOAD_2
    
    elif data.startswith('finish_'):
        # Save with just 1 photo
        ratings_data = load_ratings()
        ratings_data[upload_type] = context.user_data['photos']
        save_ratings(ratings_data)
        
        name = "РС" if upload_type == 'rs' else "РП"
        await query.edit_message_text(
            f"✅ **Фото для {name} успешно обновлено!**\n📊 Сохранено: {len(context.user_data['photos'])} фото.",
            parse_mode='Markdown'
        )
        
        # Clear user data
        context.user_data.pop('photos', None)
        context.user_data.pop('upload_type', None)
        
        return ConversationHandler.END

async def save_second_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = update.message.photo[-1].file_id
    context.user_data['photos'].append(photo_file)
    
    upload_type = context.user_data.get('upload_type')
    
    data = load_ratings()
    data[upload_type] = context.user_data['photos']
    save_ratings(data)
    
    name = "РС" if upload_type == 'rs' else "РП"
    await update.message.reply_text(
        f"✅ **Оба фото для {name} успешно обновлены!**\n📊 Сохранено: 2 фото.",
        parse_mode='Markdown'
    )
    
    # Clear user data
    context.user_data.pop('photos', None)
    context.user_data.pop('upload_type', None)
    
    return ConversationHandler.END

async def cancel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Обновление отменено.")
    context.user_data.pop('photos', None)
    context.user_data.pop('upload_type', None)
    return ConversationHandler.END

ratings_message_handler = MessageHandler(filters.Regex("^📊 Рейтинг$"), get_ratings)

upload_rs_handler = ConversationHandler(
    entry_points=[CommandHandler('set_rs', start_upload_rs)],
    states={
        PHOTO_UPLOAD_1: [MessageHandler(filters.PHOTO, save_first_photo)],
        PHOTO_UPLOAD_2: [
            MessageHandler(filters.PHOTO, save_second_photo),
            CallbackQueryHandler(handle_photo_choice, pattern="^(add_second_|finish_)")
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel_upload)]
)

upload_rp_handler = ConversationHandler(
    entry_points=[CommandHandler('set_rp', start_upload_rp)],
    states={
        PHOTO_UPLOAD_1: [MessageHandler(filters.PHOTO, save_first_photo)],
        PHOTO_UPLOAD_2: [
            MessageHandler(filters.PHOTO, save_second_photo),
            CallbackQueryHandler(handle_photo_choice, pattern="^(add_second_|finish_)")
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel_upload)]
)

# --- Group Commands for /rs and /rp (ADMIN ONLY) ---

async def show_rs_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /rs command - shows RS rating photos in group (ADMIN ONLY)"""
    # Check authorization
    is_authorized, role = await check_authorization(context, update.effective_user.id)
    
    if not is_authorized:
        await update.message.reply_text(
            "❌ **Доступ запрещён.**\nТолько менеджеры могут просматривать рейтинги в группе.",
            parse_mode='Markdown'
        )
        return
    
    data = load_ratings()
    
    if not data["rs"] or not any(data["rs"]):
        await update.message.reply_text("📉 **Рейтинг Стандартов (РС) пока не загружен.**\nПопросите менеджера обновить данные.", parse_mode='Markdown')
        return
    
    for idx, photo_id in enumerate(data["rs"], 1):
        if photo_id:
            await update.message.reply_photo(photo=photo_id, caption=f"📉 **Рейтинг Стандартов (РС) - Фото {idx}**", parse_mode='Markdown')

async def show_rp_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /rp command - shows RP rating photos in group (ADMIN ONLY)"""
    # Check authorization
    is_authorized, role = await check_authorization(context, update.effective_user.id)
    
    if not is_authorized:
        await update.message.reply_text(
            "❌ **Доступ запрещён.**\nТолько менеджеры могут просматривать рейтинги в группе.",
            parse_mode='Markdown'
        )
        return
    
    data = load_ratings()
    
    if not data["rp"] or not any(data["rp"]):
        await update.message.reply_text("🤩 **Рейтинг Продукта (РП) пока не загружен.**\nПопросите менеджера обновить данные.", parse_mode='Markdown')
        return
    
    for idx, photo_id in enumerate(data["rp"], 1):
        if photo_id:
            await update.message.reply_photo(photo=photo_id, caption=f"🤩 **Рейтинг Продукта (РП) - Фото {idx}**", parse_mode='Markdown')

# Command handlers for group usage
rs_command_handler = CommandHandler('rs', show_rs_in_group)
rp_command_handler = CommandHandler('rp', show_rp_in_group)
