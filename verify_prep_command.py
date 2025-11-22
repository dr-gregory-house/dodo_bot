import asyncio
import logging
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime

# Mock logging
logging.basicConfig(level=logging.INFO)

async def test_prep_command():
    print("Starting prep command verification...")
    
    try:
        import handlers.group_setup
    except ImportError as e:
        print(f"❌ Failed to import handlers.group_setup: {e}")
        sys.exit(1)
    
    # Mock preps
    mock_preps = "🔪 **Заготовки**..."
    
    # Patch dependencies
    with patch('handlers.group_setup.get_preps') as mock_get_preps:
        mock_get_preps.return_value = mock_preps
        
        # Mock context and update
        mock_context = MagicMock()
        mock_update = MagicMock()
        
        async def async_reply(text, parse_mode=None):
            print(f"✅ Reply sent:\n{text}")
        
        mock_update.message.reply_text = async_reply
        
        # Import and run
        from handlers.group_setup import prep_command_handler
        
        # Test 1: Before 16:00 (e.g. 14:00) -> Should be Evening Preps (Today)
        with patch('handlers.group_setup.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.hour = 14
            mock_now.weekday.return_value = 0 # Mon
            mock_datetime.now.return_value = mock_now
            
            print("\nTesting /prep at 14:00 (Mon):")
            await prep_command_handler(mock_update, mock_context)
            
            # Verify get_preps called with (0, False)
            mock_get_preps.assert_called_with(0, False)
            print("✅ Correctly requested Evening preps for Today.")
            
        # Test 2: After 16:00 (e.g. 18:00) -> Should be Morning Preps (Tomorrow)
        with patch('handlers.group_setup.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.hour = 18
            mock_now.weekday.return_value = 0 # Mon
            mock_datetime.now.return_value = mock_now
            
            print("\nTesting /prep at 18:00 (Mon):")
            await prep_command_handler(mock_update, mock_context)
            
            # Verify get_preps called with (1, True)
            mock_get_preps.assert_called_with(1, True)
            print("✅ Correctly requested Morning preps for Tomorrow.")

if __name__ == "__main__":
    asyncio.run(test_prep_command())
