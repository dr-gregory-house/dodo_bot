import asyncio
import logging
from services.sheets import get_all_employees

# Configure logging
logging.basicConfig(level=logging.INFO)

async def verify():
    print("Fetching employees...")
    employees = await get_all_employees()
    
    if "Холодный цех" in employees:
        print("SUCCESS: 'Холодный цех' found in employee list.")
    else:
        print("FAILURE: 'Холодный цех' NOT found in employee list.")
        print("Found employees:", employees)

if __name__ == "__main__":
    asyncio.run(verify())
