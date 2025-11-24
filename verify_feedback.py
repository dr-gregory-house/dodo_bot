import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock
from services.scheduler import send_feedback_notification

# Configure logging
logging.basicConfig(level=logging.INFO)

async def verify_feedback():
    print("Verifying feedback notification...")
    
    # Mock context
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    # Call the function
    await send_feedback_notification(context)
    
    # Check if send_message was called
    if context.bot.send_message.called:
        print("SUCCESS: send_message was called.")
        args, kwargs = context.bot.send_message.call_args
        print(f"Chat ID: {kwargs.get('chat_id')}")
        print(f"Message length: {len(kwargs.get('text'))}")
        print("Message content preview:")
        print(kwargs.get('text')[:100] + "...")
        
        # Verify markdown parsing
        if kwargs.get('parse_mode') == 'Markdown':
            print("SUCCESS: parse_mode is Markdown")
        else:
            print(f"FAILURE: parse_mode is {kwargs.get('parse_mode')}")
            
    else:
        print("FAILURE: send_message was NOT called.")

if __name__ == "__main__":
    asyncio.run(verify_feedback())
