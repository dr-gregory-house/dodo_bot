import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from handlers.schedule import schedule_handler

# Mock data
USER_ID = 123456789
SURNAME = "Тестовый"

# Setup users.json
with open('data/users.json', 'w', encoding='utf-8') as f:
    json.dump({str(USER_ID): SURNAME}, f)

async def test_schedule_handler():
    print("Testing schedule_handler fallback...")
    
    # Mock Update and Context
    update = MagicMock()
    update.effective_user.id = USER_ID
    update.message.reply_text = AsyncMock()
    update.callback_query = None # Ensure it's treated as message if needed, or just ignore
    
    context = MagicMock()
    context.user_data = {} # Empty user data to trigger fallback
    
    # We need to mock get_schedule to avoid actual network call
    # But schedule_handler calls show_schedule which calls get_schedule.
    # We can just check if it proceeds past the "First enter surname" check.
    
    # To do this, we can mock show_schedule in handlers.schedule
    # But we can't easily patch it here without reloading module or using patch.
    # Instead, let's just see if it calls reply_text with "Сначала введи..."
    
    # Wait, if it succeeds, it calls show_schedule.
    # If it fails, it calls reply_text("Сначала введи...")
    
    # Let's try to run it and catch the error from show_schedule (since we didn't mock get_schedule properly)
    # OR, if we see it trying to call show_schedule, we know it passed the check.
    
    try:
        await schedule_handler(update, context)
    except Exception as e:
        # It might fail inside show_schedule because we didn't mock get_schedule
        print(f"Caught expected exception (likely from show_schedule): {e}")
        
    # Check if context.user_data was updated
    if context.user_data.get('surname') == SURNAME:
        print("SUCCESS: Surname loaded from file into context.")
    else:
        print("FAILURE: Surname NOT loaded into context.")
        
    # Check if it sent the error message
    if update.message.reply_text.called:
        args, _ = update.message.reply_text.call_args
        if "Сначала введи" in args[0]:
            print("FAILURE: Handler asked to register despite user existing in file.")
        else:
            print(f"Handler replied with: {args[0]}")

if __name__ == "__main__":
    asyncio.run(test_schedule_handler())
