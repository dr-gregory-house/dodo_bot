
import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())
from services.sheets import get_who_on_shift

async def test_who_on_shift():
    # Use today's date based on system time: 23.12.2025
    today_date = "23.12"
    print(f"--- Testing 'Who is working today' for {today_date} ---\n")
    
    # Test for a generic user (no surname)
    result = await get_who_on_shift(today_date)
    print("Result for all employees:")
    print(result)
    
    print("\n" + "="*40 + "\n")
    
    # Test for a specific user to see if 'Your shift' header appears
    # From previous tests, we know 'Ахмитенко' is a manager
    test_surname = "Ахмитенко"
    print(f"--- Testing 'Who is working today' for {today_date} (User: {test_surname}) ---\n")
    result_with_user = await get_who_on_shift(today_date, surname=test_surname)
    print(result_with_user)

if __name__ == "__main__":
    asyncio.run(test_who_on_shift())
