"""
Voice message handler for sending audio to group.
Only available for authorized user (anubhav/мишра).
"""
import json
import os
import logging
import tempfile
import subprocess
from telegram import Update, InputFile
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


def get_audio_duration(file_path: str) -> int:
    """Get audio duration in seconds using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        return int(duration)
    except Exception as e:
        logger.warning(f"Could not get duration: {e}")
        return 0


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
    
    # Set test mode to False by default
    context.user_data['voice_test_mode'] = False
    
    await update.message.reply_text(
        "🎤 Отправьте мне голосовое сообщение или аудиофайл.\n"
        "Я перешлю его в группу.\n\n"
        "Отправьте /cancel для отмены."
    )
    return WAITING_FOR_AUDIO


async def voice_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /voice_test command - test mode (sends back to user, not group)."""
    # Only works in private chat
    if update.effective_chat.type != 'private':
        await update.message.reply_text("❌ Эту команду можно использовать только в личных сообщениях.")
        return ConversationHandler.END
    
    # Check authorization
    if not await is_authorized(update, context):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return ConversationHandler.END
    
    # Set test mode to True
    context.user_data['voice_test_mode'] = True
    
    await update.message.reply_text(
        "🧪 РЕЖИМ ТЕСТИРОВАНИЯ\n\n"
        "Отправьте аудиофайл - я конвертирую его и отправлю обратно вам.\n"
        "Это позволит проверить, корректно ли отображается волна.\n\n"
        "Отправьте /cancel для отмены."
    )
    return WAITING_FOR_AUDIO


async def receive_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle received audio/voice file."""
    test_mode = context.user_data.get('voice_test_mode', False)
    group_id = get_group_id()
    
    if not test_mode and not group_id:
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
        
        await update.message.reply_text("⏳ Обрабатываю аудио...")
        
        # Download the file
        telegram_file = await file.get_file()
        file_bytes = await telegram_file.download_as_bytearray()
        
        # Save input to temp file
        with tempfile.NamedTemporaryFile(suffix=".input", delete=False) as input_tmp:
            input_tmp.write(file_bytes)
            input_path = input_tmp.name
            
        output_path = input_path + ".oga"  # .oga extension for Ogg Audio
        
        try:
            # Convert to OGG Opus using ffmpeg - optimized for Telegram voice messages
            # -map 0:a extracts ONLY audio (ignores album art/video that breaks Telegram)
            cmd = [
                'ffmpeg', '-y', '-i', input_path,
                '-map', '0:a',  # Extract only audio stream (fixes MP3s with embedded album art)
                '-c:a', 'libopus',
                '-b:a', '48k',  # Bitrate for voice
                '-vbr', 'on',
                '-compression_level', '10',
                '-application', 'voip',  # Voice-optimized encoding
                '-ac', '1',  # Mono
                '-ar', '48000',  # 48kHz sample rate (required for Opus)
                '-f', 'ogg',  # OGG container
                output_path
            ]
            
            process = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
            
            # Get duration of the converted file
            duration = get_audio_duration(output_path)
            file_size = os.path.getsize(output_path)
            
            logger.info(f"Converted audio: duration={duration}s, size={file_size} bytes")
            
            if test_mode:
                # Test mode: send back to user
                # Send raw bytes directly (proven to work in standalone tests)
                with open(output_path, 'rb') as audio_file:
                    voice_bytes = audio_file.read()
                
                logger.info(f"SENDING: bytes_len={len(voice_bytes)}, duration_param={duration}")
                
                msg = await context.bot.send_voice(
                    chat_id=update.effective_chat.id,
                    voice=voice_bytes,
                    duration=duration,
                    caption=f"🧪 Тест: duration={duration}s, size={file_size}bytes"
                )
                
                # Log what API returned
                if msg.voice:
                    logger.info(f"API RETURNED: voice.duration={msg.voice.duration}, voice.file_size={msg.voice.file_size}")
                else:
                    logger.warning("API RETURNED: NO VOICE OBJECT!")
                
                await update.message.reply_text(
                    "✅ Тестовое сообщение отправлено!\n\n"
                    "Проверьте:\n"
                    "• Отображается ли волна?\n"
                    "• Воспроизводится ли на телефоне?\n\n"
                    "Если всё ок - используйте /voice для отправки в группу."
                )
                logger.info(f"Test voice sent to user {update.effective_user.id}")
            else:
                # Normal mode: send to group
                # Send raw bytes directly (proven to work in standalone tests)
                with open(output_path, 'rb') as audio_file:
                    voice_bytes = audio_file.read()
                
                await context.bot.send_voice(
                    chat_id=int(group_id),
                    voice=voice_bytes,
                    duration=duration,
                    caption="📢 Итоги дня от dodo_bot 🦤"
                )
                await update.message.reply_text("✅ Голосовое сообщение успешно отправлено в группу!")
                logger.info(f"Voice message sent to group {group_id} by user {update.effective_user.id}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e.stderr.decode()}")
            await update.message.reply_text("❌ Ошибка при конвертации аудио. Попробуйте другой формат.")
        finally:
            # Cleanup temp files
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        
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
    entry_points=[
        CommandHandler("voice", voice_command),
        CommandHandler("voice_test", voice_test_command),
    ],
    states={
        WAITING_FOR_AUDIO: [
            MessageHandler(filters.VOICE | filters.AUDIO | filters.Document.ALL, receive_audio),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
