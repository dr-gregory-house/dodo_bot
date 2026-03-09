import logging
import os
import base64
from datetime import datetime
import pytz
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from services.message_collector import get_daily_data

logger = logging.getLogger(__name__)

FEEDBACK_FILE = 'data/feedback.text'

async def analyze_feedback():
    """
    Analyze collected messages using OpenAI-compatible LLM and generate feedback summary.
    Saves result to data/feedback.text.
    """
    try:
        if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_openai_api_key_here':
            logger.warning("OpenAI API key not configured. Skipping feedback analysis.")
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
        
        # Call OpenAI API
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL,
            )
            
            # Build message content (text + images for vision models)
            prompt_text = create_analysis_prompt(text_messages, image_data)
            
            # Build content parts for the user message
            content_parts = [{"type": "text", "text": prompt_text}]
            
            # Add images as base64 for vision-capable models
            for img_info in image_data:
                file_path = img_info.get('file_path')
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as img_file:
                            img_bytes = img_file.read()
                        b64_image = base64.b64encode(img_bytes).decode('utf-8')
                        
                        # Determine mime type
                        ext = os.path.splitext(file_path)[1].lower()
                        mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'}
                        mime_type = mime_map.get(ext, 'image/jpeg')
                        
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}"
                            }
                        })
                        
                        # Add context for this image
                        img_context = f"\n[Изображение от {img_info['user']} в {img_info['timestamp']}"
                        if img_info['caption']:
                            img_context += f", подпись: {img_info['caption']}"
                        img_context += "]"
                        content_parts.append({"type": "text", "text": img_context})
                        
                    except Exception as e:
                        logger.warning(f"Could not load image {file_path}: {e}")
            
            # Generate response
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты - Dodo_bot, аналитик обратной связи для пиццерии Додо Пицца."},
                    {"role": "user", "content": content_parts}
                ],
                max_tokens=2000,
                temperature=0.7,
            )
            
            summary = response.choices[0].message.content
            
            # Save to feedback.text
            with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            logger.info(f"Feedback analysis completed with {len(image_data)} images. Summary saved to {FEEDBACK_FILE}")
            return True
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
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
    
    for i, msg in enumerate(text_messages, 1):
        prompt += f"\n{i}. [{msg['user']}] {msg['timestamp']}: {msg['text']}"
    
    if image_data:
        prompt += f"\n\n**Также получено изображений: {len(image_data)} шт.**"
        prompt += "\n(Изображения прикреплены ниже для визуального анализа. Проанализируй их содержимое!)"
    
    prompt += """

**Твой ответ должен быть готов к отправке в группу (НЕ включай заголовки типа "Анализ за..." или технические детали).**

Начни с эмодзи и приветствия (например: "👋 *Привет, команда*! Dodo_bot на связи."), затем сразу к аналитике.
Используй Markdown форматирование (жирный текст *текст*, курсив _текст_).
Escape специальных символов для Telegram Markdown при необходимости (например, _ в Dodo\\_bot).
"""
    
    return prompt
