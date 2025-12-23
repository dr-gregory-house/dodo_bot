
import asyncio
import sys
import os

sys.path.append(os.getcwd())
from services.sheets import get_preps

async def test_preps():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Test for today (Tuesday = index 1)
    day_idx = 1 
    print(f"--- Testing Preps for {days[day_idx]} ---")
    
    print("\n[Morning Prep]")
    morning = await get_preps(day_idx, is_morning=True)
    print(morning)
    
    print("\n[Evening Prep]")
    evening = await get_preps(day_idx, is_morning=False)
    print(evening)

if __name__ == "__main__":
    asyncio.run(test_preps())
