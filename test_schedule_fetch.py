
import asyncio
import logging
import sys
import os

# Add current directory to path so we can import services
sys.path.append(os.getcwd())

from services.sheet_manager import sheet_manager
from services.sheets import get_schedule, get_shifts_for_date, get_all_employees

logging.basicConfig(level=logging.INFO)

async def test_schedule():
    print("--- Testing Sheet Discovery ---")
    sheets = await sheet_manager.get_sheets(force_refresh=True)
    print(f"Found {len(sheets)} sheets:")
    for s in sheets:
        print(f"  - {s['name']} (GID: {s['gid']})")
    
    if not sheets:
        print("No sheets found! Discovery might be broken.")
        return

    print("\n--- Testing Specific Date Fetch ---")
    # Let's try to find a date in the first sheet
    import csv
    import io
    import urllib.request
    
    first_gid = sheets[0]['gid']
    url = f"https://docs.google.com/spreadsheets/d/1hbvUroW0SxAbTbsn0nn-9wJyYKz-zLDJQ_PS7b83SzA/export?format=csv&gid={first_gid}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
    
    reader = list(csv.reader(io.StringIO(content)))
    if len(reader) > 0:
        dates = [d.strip() for d in reader[0] if d.strip() and '.' in d]
        print(f"Dates found in first sheet ({sheets[0]['name']}): {dates}")
        
        if dates:
            test_date = dates[0]
            print(f"Fetching shifts for {test_date}...")
            shifts = await get_shifts_for_date(test_date)
            print(f"Found {len(shifts)} shifts on {test_date}:")
            for shift in shifts[:5]: # Show first 5
                print(f"  - {shift['name']} ({shift['role']}): {shift['shift']}")
            if len(shifts) > 5:
                print(f"  ... and {len(shifts)-5} more.")

    print("\n--- Testing Employee Fetch ---")
    employees = await get_all_employees()
    print(f"Total unique employees found: {len(employees)}")
    print(f"First 10 employees: {employees[:10]}")

    print("\n--- Testing Personal Schedule ---")
    if employees:
        test_emp = employees[0]
        # Get just the surname if possible
        surname = test_emp.split()[0]
        print(f"Fetching schedule for: {surname}")
        personal_schedules = await get_schedule(surname)
        print(f"Found {len(personal_schedules)} weekly schedules for {surname}.")
        for ps in personal_schedules:
            print(f"\nSheet: {ps['sheet_name']}")
            print(ps['text'])

if __name__ == "__main__":
    asyncio.run(test_schedule())
