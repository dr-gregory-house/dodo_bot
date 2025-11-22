import asyncio
import logging
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Mock logging
logging.basicConfig(level=logging.INFO)

# Import services.scheduler
try:
    import services.scheduler
except ImportError:
    pass

async def test_group_notification():
    print("Starting group notification verification...")
    
    # Mock data
    mock_group = {'group_id': '-100123456789'}
    mock_preps = "🔪 **Заготовки на Понедельник** (☀️ Утро)\n━━━━━━━━━━━━\n• **Тесто**: `10` лекс."
    
    # Patch dependencies
    with patch('services.scheduler.load_json') as mock_load:
        mock_load.return_value = mock_group
        
        with patch('services.scheduler.get_preps') as mock_get_preps:
            mock_get_preps.return_value = mock_preps
            
            # Mock context
            mock_context = MagicMock()
            
            async def async_send_message(chat_id, text, parse_mode):
                print(f"✅ Notification sent to group {chat_id}:\n{text}")
            
            mock_context.bot.send_message = async_send_message
            
            # Import and run
            from services.scheduler import send_preps_notification
            
            # Test Morning (mock time to 9:00)
            with patch('services.scheduler.datetime') as mock_datetime:
                mock_now = MagicMock()
                mock_now.hour = 9
                mock_now.weekday.return_value = 0
                mock_datetime.now.return_value = mock_now
                
                print("\nTesting Morning Notification:")
                await send_preps_notification(mock_context)
                
            # Test Evening (mock time to 17:00)
            with patch('services.scheduler.datetime') as mock_datetime:
                mock_now = MagicMock()
                mock_now.hour = 17
                mock_now.weekday.return_value = 0
                mock_datetime.now.return_value = mock_now
                
                print("\nTesting Evening Notification:")
                await send_preps_notification(mock_context)

if __name__ == "__main__":
    asyncio.run(test_group_notification())
