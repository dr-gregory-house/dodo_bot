import logging
import json
import os
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from services.message_collector import save_message, save_image

logger = logging.getLogger(__name__)

GROUP_FILE = 'data/group.json'

def load_group_id():
    """Load the configured group ID."""
    if not os.path.exists(GROUP_FILE):
        return None
    try:
        with open(GROUP_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('group_id')
    except:
        return None

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler to capture all text messages from the configured group.
    Runs silently without responding.
    """
    try:
        # Only process messages from the configured group
        group_id = load_group_id()
        if not group_id:
            return
        
        chat_id = str(update.effective_chat.id)
        if chat_id != group_id:
            return
        
        # Don't capture bot commands
        if update.message.text and update.message.text.startswith('/'):
            return
        
        # Save the message
        await save_message(update, context)
        
    except Exception as e:
        logger.error(f"Error in text_message_handler: {e}")

async def photo_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler to capture all photo messages from the configured group.
    Runs silently without responding.
    """
    try:
        # Only process messages from the configured group
        group_id = load_group_id()
        if not group_id:
            return
        
        chat_id = str(update.effective_chat.id)
        if chat_id != group_id:
            return
        
        # Save the image
        await save_image(update, context)
        
    except Exception as e:
        logger.error(f"Error in photo_message_handler: {e}")

# Create handler instances
text_collection_handler = MessageHandler(
    filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
    text_message_handler
)

photo_collection_handler = MessageHandler(
    filters.ChatType.GROUPS & filters.PHOTO,
    photo_message_handler
)
