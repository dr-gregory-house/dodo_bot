"""
Voice message handler for sending audio to group.
Only available for authorized user (anubhav/мишра).
"""
import json
import os
import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

logger = logging.getLogger(__name__)

GROUP_FILE = 'data/group.json'
WAITING_FOR_AUDIO = 1

# Authorized user check (by surname in user data)
AUTHORIZED_SURNAMES = ['мишра']


def get_group_id() -> str | None:
    """Get the saved group ID from file."""
    try:
        if os.path.exists(GROUP_FILE):
            with open(GROUP_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('group_id')
    except Exception as e:
        logger.error(f"Error reading group file: {e}")
    return None


async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is authorized to use /voice command."""
    user_id = update.effective_user.id
    surname = context.user_data.get('surname')
    
    # Try to load from users.json if not in context
    if not surname:
        try:
            if os.path.exists('data/users.json'):
                with open('data/users.json', 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    surname = users.get(str(user_id))
        except:
            pass
    
    if surname:
        surname_lower = surname.lower()
        for auth_surname in AUTHORIZED_SURNAMES:
            if auth_surname in surname_lower:
                return True
    
    return False


async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /voice command - start conversation."""
    # Only works in private chat
    if update.effective_chat.type != 'private':
        await update.message.reply_text("❌ Эту команду можно использовать только в личных сообщениях.")
        return ConversationHandler.END
    
    # Check authorization
    if not await is_authorized(update, context):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return ConversationHandler.END
    
    # Check if group is configured
    group_id = get_group_id()
    if not group_id:
        await update.message.reply_text("❌ Группа не настроена. Используйте /set_group в группе.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🎤 Отправьте мне голосовое сообщение или аудиофайл.\n"
        "Я перешлю его в группу.\n\n"
        "Отправьте /cancel для отмены."
    )
    return WAITING_FOR_AUDIO


async def receive_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle received audio/voice file."""
    group_id = get_group_id()
    
    if not group_id:
        await update.message.reply_text("❌ Группа не настроена.")
        return ConversationHandler.END
    
    try:
        # Get the audio file (voice or audio)
        if update.message.voice:
            file = update.message.voice
            file_type = "voice"
        elif update.message.audio:
            file = update.message.audio
            file_type = "audio"
        elif update.message.document:
            # Check if it's an audio file
            mime = update.message.document.mime_type or ""
            if mime.startswith("audio/") or mime == "application/ogg":
                file = update.message.document
                file_type = "document"
            else:
                await update.message.reply_text("❌ Пожалуйста, отправьте аудиофайл.")
                return WAITING_FOR_AUDIO
        else:
            await update.message.reply_text("❌ Пожалуйста, отправьте голосовое сообщение или аудиофайл.")
            return WAITING_FOR_AUDIO
        
        # Download the file
        telegram_file = await file.get_file()
        file_bytes = await telegram_file.download_as_bytearray()
        
        # Send to group as voice message
        from io import BytesIO
        audio_buffer = BytesIO(bytes(file_bytes))
        audio_buffer.name = "voice.ogg"  # Telegram needs a filename
        
        await context.bot.send_voice(
            chat_id=int(group_id),
            voice=audio_buffer,
            caption="📢 Итоги дня от dodo_bot 🦤"
        )
        
        await update.message.reply_text("✅ Голосовое сообщение отправлено в группу!")
        logger.info(f"Voice message sent to group {group_id} by user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error sending voice to group: {e}")
        await update.message.reply_text(f"❌ Ошибка при отправке: {e}")
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END


# Create the conversation handler
voice_handler = ConversationHandler(
    entry_points=[CommandHandler("voice", voice_command)],
    states={
        WAITING_FOR_AUDIO: [
            MessageHandler(filters.VOICE | filters.AUDIO | filters.Document.ALL, receive_audio),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
