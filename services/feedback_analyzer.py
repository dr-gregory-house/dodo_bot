import logging
import os
from datetime import datetime
import pytz
from config import GEMINI_API_KEY, GEMINI_MODEL
from services.message_collector import get_daily_data

logger = logging.getLogger(__name__)

FEEDBACK_FILE = 'data/feedback.text'

async def analyze_feedback():
    """
    Analyze collected messages using Gemini LLM and generate feedback summary.
    Saves result to data/feedback.text.
    """
    try:
        if not GEMINI_API_KEY or GEMINI_API_KEY == 'your_gemini_api_key_here':
            logger.warning("Gemini API key not configured. Skipping feedback analysis.")
            return False
        
        # Get today's collected messages
        messages = get_daily_data()
        
        if not messages:
            logger.info("No messages collected today. Skipping feedback analysis.")
            return False
        
        # Filter and prepare messages for analysis
        text_messages = []
        image_data = []
        
        for msg in messages:
            if msg.get('type') == 'image':
                image_data.append({
                    'user': f"{msg.get('first_name', '')} {msg.get('last_name', '')}".strip(),
                    'caption': msg.get('caption', ''),
                    'timestamp': msg.get('timestamp', ''),
                    'file_path': msg.get('file_path', '')
                })
            elif msg.get('text'):
                text_messages.append({
                    'user': f"{msg.get('first_name', '')} {msg.get('last_name', '')}".strip(),
                    'text': msg.get('text', ''),
                    'timestamp': msg.get('timestamp', '')
                })
        
        # Call Gemini API with multimodal content
        try:
            import google.generativeai as genai
            from PIL import Image
            
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            # Create content parts: text prompt + images
            content_parts = []
            
            # Add text prompt
            prompt_text = create_analysis_prompt(text_messages, image_data)
            content_parts.append(prompt_text)
            
            # Add images
            for img_info in image_data:
                file_path = img_info.get('file_path')
                if file_path and os.path.exists(file_path):
                    try:
                        img = Image.open(file_path)
                        content_parts.append(img)
                        # Add context for this image
                        img_context = f"\n[Изображение от {img_info['user']} в {img_info['timestamp']}"
                        if img_info['caption']:
                            img_context += f", подпись: {img_info['caption']}"
                        img_context += "]"
                        content_parts.append(img_context)
                    except Exception as e:
                        logger.warning(f"Could not load image {file_path}: {e}")
            
            # Generate response with all content
            response = model.generate_content(content_parts)
            summary = response.text
            
            # Save to feedback.text
            with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            logger.info(f"Feedback analysis completed with {len(image_data)} images. Summary saved to {FEEDBACK_FILE}")
            return True
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error in analyze_feedback: {e}")
        return False

def create_analysis_prompt(text_messages, image_data):
    """Create the prompt for LLM analysis."""
    
    tz = pytz.timezone('Europe/Moscow')
    today = datetime.now(tz).strftime("%d.%m.%Y")
    
    prompt = f"""Ты - Dodo_bot, аналитик обратной связи для пиццерии Додо Пицца. 

Твоя задача - проанализировать сообщения и изображения из рабочей группы за {today} и создать краткое резюме для команды.

**ВАЖНО**: 
- Пиши на русском языке
- Используй дружелюбный, но профессиональный тон
- Будь конкретным и конструктивным
- Выдели самые важные моменты
- АНАЛИЗИРУЙ ИЗОБРАЖЕНИЯ: если есть фото проблем с едой, качеством, чистотой - опиши что видишь
- Используй эмодзи для визуального оформления (⚠️ 📉 ⚖️ 📦 ✅ и т.д.)
- Формат сообщения должен быть похож на существующий стиль общения бота
- В конце можешь добавить мотивирующую цитату или фразу

**Структура анализа:**
1. Приветствие команде
2. Что было хорошего/позитивного (если есть)
3. Основные проблемы и жалобы (если есть)
4. Конкретные рекомендации по улучшению
5. Мотивирующее заключение

**Собранные текстовые сообщения ({len(text_messages)} шт.):**
"""
    
    for i, msg in enumerate(text_messages, 1):  # Отправляем все сообщения
        prompt += f"\n{i}. [{msg['user']}] {msg['timestamp']}: {msg['text']}"
    
    if image_data:
        prompt += f"\n\n**Также получено изображений: {len(image_data)} шт.**"
        prompt += "\n(Изображения прикреплены ниже для визуального анализа. Проанализируй их содержимое!)"
    
    prompt += """

**Твой ответ должен быть готов к отправке в группу (НЕ включай заголовки типа "Анализ за..." или технические детали).**

Начни с эмодзи и приветствия (например: "👋 *Привет, команда*! Dodo_bot на связи."), затем сразу к аналитике.
Используй Markdown форматирование (жирный текст *текст*, курсив _текст_).
Escape специальных символов для Telegram Markdown при необходимости (например, _ в Dodo_bot).
"""
    
    return prompt
