import logging
import json
import os
from datetime import datetime
from pathlib import Path
from telegram import Update, PhotoSize
from telegram.ext import ContextTypes
import pytz

logger = logging.getLogger(__name__)

MESSAGES_DIR = 'data/messages'
IMAGES_DIR = 'data/images'

def get_current_date():
    """Get current date in Moscow timezone."""
    tz = pytz.timezone('Europe/Moscow')
    return datetime.now(tz).strftime("%Y-%m-%d")

def get_messages_file():
    """Get the path to today's messages file."""
    date_str = get_current_date()
    os.makedirs(MESSAGES_DIR, exist_ok=True)
    return os.path.join(MESSAGES_DIR, f'daily_messages_{date_str}.json')

def get_images_dir():
    """Get the path to today's images directory."""
    date_str = get_current_date()
    images_path = os.path.join(IMAGES_DIR, date_str)
    os.makedirs(images_path, exist_ok=True)
    return images_path

def load_daily_messages():
    """Load today's messages from file."""
    filepath = get_messages_file()
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading messages from {filepath}: {e}")
        return []

def save_daily_messages(messages):
    """Save messages to today's file."""
    filepath = get_messages_file()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving messages to {filepath}: {e}")

async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save a text message to daily log."""
    try:
        message = update.message
        if not message or not message.text:
            return
        
        tz = pytz.timezone('Europe/Moscow')
        timestamp = datetime.now(tz).isoformat()
        
        message_data = {
            'timestamp': timestamp,
            'user_id': message.from_user.id,
            'username': message.from_user.username or 'N/A',
            'first_name': message.from_user.first_name or 'N/A',
            'last_name': message.from_user.last_name or 'N/A',
            'text': message.text,
            'message_id': message.message_id
        }
        
        messages = load_daily_messages()
        messages.append(message_data)
        save_daily_messages(messages)
        
        logger.info(f"Saved message from {message.from_user.first_name}: {message.text[:50]}...")
        
    except Exception as e:
        logger.error(f"Error saving message: {e}")

async def save_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save an image message to daily log."""
    try:
        message = update.message
        if not message or not message.photo:
            return
        
        tz = pytz.timezone('Europe/Moscow')
        timestamp = datetime.now(tz).isoformat()
        
        # Get the largest photo
        photo: PhotoSize = message.photo[-1]
        
        # Download the photo
        file = await context.bot.get_file(photo.file_id)
        images_dir = get_images_dir()
        
        # Create filename with timestamp and user info
        safe_timestamp = timestamp.replace(':', '-').replace('.', '_')
        filename = f"{safe_timestamp}_{message.from_user.id}.jpg"
        filepath = os.path.join(images_dir, filename)
        
        await file.download_to_drive(filepath)
        
        # Save metadata
        image_data = {
            'timestamp': timestamp,
            'user_id': message.from_user.id,
            'username': message.from_user.username or 'N/A',
            'first_name': message.from_user.first_name or 'N/A',
            'last_name': message.from_user.last_name or 'N/A',
            'caption': message.caption or '',
            'message_id': message.message_id,
            'file_path': filepath,
            'file_id': photo.file_id
        }
        
        messages = load_daily_messages()
        messages.append({
            'type': 'image',
            **image_data
        })
        save_daily_messages(messages)
        
        logger.info(f"Saved image from {message.from_user.first_name} to {filepath}")
        
    except Exception as e:
        logger.error(f"Error saving image: {e}")

def get_daily_data():
    """Get all collected messages and images for today."""
    messages = load_daily_messages()
    return messages

def reset_daily_data():
    """Clean up old message files (keep last 7 days)."""
    try:
        # Clean up old message files
        if os.path.exists(MESSAGES_DIR):
            for filename in os.listdir(MESSAGES_DIR):
                if filename.startswith('daily_messages_'):
                    filepath = os.path.join(MESSAGES_DIR, filename)
                    # Get file modification time
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    days_old = (datetime.now() - file_time).days
                    
                    # Delete files older than 7 days
                    if days_old > 7:
                        os.remove(filepath)
                        logger.info(f"Deleted old message file: {filename}")
        
        # Clean up old image directories
        if os.path.exists(IMAGES_DIR):
            for dirname in os.listdir(IMAGES_DIR):
                dirpath = os.path.join(IMAGES_DIR, dirname)
                if os.path.isdir(dirpath):
                    # Check if directory is older than 7 days
                    dir_time = datetime.fromtimestamp(os.path.getmtime(dirpath))
                    days_old = (datetime.now() - dir_time).days
                    
                    if days_old > 7:
                        import shutil
                        shutil.rmtree(dirpath)
                        logger.info(f"Deleted old images directory: {dirname}")
        
        logger.info("Daily data cleanup completed")
        
    except Exception as e:
        logger.error(f"Error resetting daily data: {e}")
