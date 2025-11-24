import asyncio
import logging
from services.sheets import get_all_employees

logging.basicConfig(level=logging.INFO)

async def main():
    print("Fetching employees...")
    employees = await get_all_employees()
    print(f"Found {len(employees)} employees:")
    for emp in employees:
        print(f"- {emp}")

if __name__ == "__main__":
    asyncio.run(main())
