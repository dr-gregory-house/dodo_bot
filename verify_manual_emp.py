import asyncio
import logging
from services.sheets import get_all_employees

# Configure logging
logging.basicConfig(level=logging.INFO)

async def verify():
    print("--- Testing Manual Employee Addition ---")
    employees = await get_all_employees()
    
    target = "Лилия Смолкина"
    if target in employees:
        print(f"✅ Found '{target}' in employee list.")
    else:
        print(f"❌ '{target}' NOT found in employee list.")
        
    print(f"Total employees: {len(employees)}")

if __name__ == "__main__":
    asyncio.run(verify())
