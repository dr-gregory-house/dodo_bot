#!/usr/bin/env python3
"""Generate a list of employees who have a shift today but are not subscribed.

This script:
1. Gets today's date
2. Fetches all employees working today from the schedule
3. Reads the list of not-subscribed employees
4. Finds the intersection (employees on shift today who are not subscribed)
5. Saves the result to data/on_shift.json
"""

import asyncio
import json
import os
from datetime import datetime
from services.sheets import get_shifts_for_date

NOT_SUBSCRIBED_PATH = os.path.join(os.path.dirname(__file__), "data", "not_subscribed.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "on_shift.json")

async def main():
    # Get today's date in DD.MM format
    today = datetime.now().strftime("%d.%m")
    
    print(f"Checking shifts for {today}...")
    
    # Fetch all employees working today
    shifts_today = await get_shifts_for_date(today)
    
    if not shifts_today:
        print(f"No shifts found for {today}")
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return
    
    # Extract employee names from shifts
    employees_on_shift = {shift['name'].strip() for shift in shifts_today}
    print(f"Found {len(employees_on_shift)} employees on shift today")
    
    # Load not-subscribed employees
    not_subscribed = set()
    if os.path.exists(NOT_SUBSCRIBED_PATH):
        with open(NOT_SUBSCRIBED_PATH, "r", encoding="utf-8") as f:
            try:
                not_subscribed_list = json.load(f)
                not_subscribed = {name.strip() for name in not_subscribed_list}
                print(f"Found {len(not_subscribed)} not-subscribed employees")
            except json.JSONDecodeError:
                print("Failed to parse not_subscribed.json")
    else:
        print(f"Warning: {NOT_SUBSCRIBED_PATH} not found. Run not_subscribed.py first.")
    
    # Find employees on shift today who are not subscribed
    on_shift_not_subscribed = []
    for shift in shifts_today:
        name = shift['name'].strip()
        if name in not_subscribed:
            on_shift_not_subscribed.append({
                "name": name,
                "role": shift['role'],
                "shift": shift['shift']
            })
    
    # Sort by role and name
    role_priority = {
        'менеджер': 0,
        'наставник': 1,
        'инструктор': 2,
        'универсал': 3,
        'пиццамейкер': 4,
        'кассир': 5,
        'курьер': 6,
        'стажёр': 7
    }
    
    on_shift_not_subscribed.sort(key=lambda x: (role_priority.get(x['role'], 99), x['name']))
    
    # Write result to JSON file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(on_shift_not_subscribed, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Found {len(on_shift_not_subscribed)} employees on shift today who are NOT subscribed")
    print(f"📁 Saved to {OUTPUT_PATH}")
    
    # Print summary
    if on_shift_not_subscribed:
        print("\n📋 Summary:")
        for emp in on_shift_not_subscribed:
            print(f"  - {emp['name']} ({emp['role']}) - {emp['shift']}")

if __name__ == "__main__":
    asyncio.run(main())
