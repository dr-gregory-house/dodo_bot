"""
Text message handler for sending manual text messages to group.
Only available for authorized user (anubhav/мишра).
"""
import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from handlers.voice import get_group_id, is_authorized

logger = logging.getLogger(__name__)

WAITING_FOR_TEXT = 1


async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /announce command - start conversation."""
    # Only works in private chat
    if update.effective_chat.type != 'private':
        await update.message.reply_text("❌ This command can only be used in private messages.")
        return ConversationHandler.END
    
    # Check authorization
    if not await is_authorized(update, context):
        await update.message.reply_text("❌ You do not have access to this command.")
        return ConversationHandler.END
    
    # Check if group is configured
    group_id = get_group_id()
    if not group_id:
        await update.message.reply_text("❌ Group is not configured. Use /set_group in the group.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "✍️ Send me a text message and I will forward it to the group.\n\n"
        "Send /cancel to abort."
    )
    return WAITING_FOR_TEXT


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle received text."""
    group_id = get_group_id()
    
    if not group_id:
        await update.message.reply_text("❌ Group is not configured.")
        return ConversationHandler.END
    
    try:
        if not update.message.text:
            await update.message.reply_text("❌ Please send a text message.")
            return WAITING_FOR_TEXT
            
        text_to_send = update.message.text
        
        await context.bot.send_message(
            chat_id=int(group_id),
            text=text_to_send
        )
        await update.message.reply_text("✅ Message successfully sent to the group!")
        logger.info(f"Text message sent to group {group_id} by user {update.effective_user.id}")
            
    except Exception as e:
        logger.error(f"Error sending text to group: {e}")
        await update.message.reply_text(f"❌ Error sending message: {e}")
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


# Create the conversation handler
announce_handler = ConversationHandler(
    entry_points=[CommandHandler("announce", announce_command)],
    states={
        WAITING_FOR_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
