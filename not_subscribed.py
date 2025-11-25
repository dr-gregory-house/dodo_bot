#!/usr/bin/env python3
"""Generate a list of employees from the schedule (graphic) that are not subscribed.

This script uses the existing `get_all_employees` function to fetch all employee names
from the Google Sheets schedule, then reads `data/users.json` to get the currently
subscribed users. The difference is written to `data/not_subscribed.json`.
"""

import asyncio
import json
import os
from services.sheets import get_all_employees

USERS_PATH = os.path.join(os.path.dirname(__file__), "data", "users.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "not_subscribed.json")

async def main():
    # Fetch all employee names from the schedule (graphic)
    all_employees = await get_all_employees()

    # Load subscribed users from users.json (values are names)
    subscribed_names = set()
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            try:
                users_data = json.load(f)
                # users.json maps telegram_id -> "Surname Name"
                subscribed_names = {name.strip() for name in users_data.values()}
            except json.JSONDecodeError:
                print("Failed to parse users.json")

    # Compute not‑subscribed employees
    not_subscribed = [emp for emp in all_employees if emp not in subscribed_names]

    # Write result to JSON file for easy consumption
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(not_subscribed, f, ensure_ascii=False, indent=2)

    print(f"Found {len(not_subscribed)} not‑subscribed employees. Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
