import asyncio
import logging
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Mock logging
logging.basicConfig(level=logging.INFO)

# Import the function to test
# We need to ensure services.scheduler is imported so patch can find it
try:
    import services.scheduler
except ImportError:
    # If it fails (e.g. due to missing dependencies in environment), we might need to mock them first
    pass

async def test_notification():
    print("Starting verification...")
    
    # Mock data
    mock_users = {'12345': 'TestUser'}
    mock_notifications = {}
    
    # Mock shift starting in 30 mins
    now = datetime.now()
    shift_start = now + timedelta(minutes=30)
    shift_str = f"{shift_start.hour}:{shift_start.minute:02d}-{shift_start.hour+8}:{shift_start.minute:02d}"
    
    mock_shifts = [{
        'name': 'TestUser',
        'role': 'pizzamaker',
        'shift': shift_str
    }]
    
    print(f"Current time: {now.strftime('%H:%M')}")
    print(f"Mock shift: {shift_str}")
    
    # Patch dependencies
    with patch('services.scheduler.load_json') as mock_load:
        # Return users for first call, empty dict for second (notifications)
        mock_load.side_effect = [mock_users, mock_notifications]
        
        with patch('services.scheduler.save_json') as mock_save:
            with patch('services.scheduler.get_shifts_for_date') as mock_get_shifts:
                mock_get_shifts.return_value = mock_shifts
                
                # Mock context
                mock_context = MagicMock()
                mock_context.bot.send_message = MagicMock(side_effect=lambda chat_id, text: asyncio.sleep(0)) # Async mock
                
                # Import and run
                from services.scheduler import check_shifts_and_notify
                
                # We need to await the mock send_message if it's async, but MagicMock isn't async by default.
                # The code awaits context.bot.send_message.
                # So we need an AsyncMock.
                
                async def async_send_message(chat_id, text):
                    print(f"✅ Notification sent to {chat_id}: {text}")
                
                mock_context.bot.send_message = async_send_message
                
                await check_shifts_and_notify(mock_context)
                
                # Verify save_json was called (updating notifications)
                if mock_save.called:
                    print("✅ Notifications file updated.")
                else:
                    print("❌ Notifications file NOT updated.")

if __name__ == "__main__":
    asyncio.run(test_notification())
