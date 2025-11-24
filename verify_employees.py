import asyncio
import logging
from services.sheets import get_all_employees

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("Fetching employees...")
    employees = await get_all_employees()
    
    print(f"\nTotal employees found: {len(employees)}")
    print("-" * 30)
    for emp in employees:
        print(emp)
    print("-" * 30)
    
    # Verification checks
    print("\nVerification Results:")
    
    # Check blacklist
    blacklisted = ["Куйкин", "Антуфьева"]
    for name in blacklisted:
        found = any(name.lower() in emp.lower() for emp in employees)
        status = "❌ FAILED" if found else "✅ PASSED"
        print(f"Blacklist check for '{name}': {status}")
        
    # Check duplicates
    davydova_count = sum(1 for emp in employees if "давыдова" in emp.lower())
    status = "✅ PASSED" if davydova_count == 1 else f"❌ FAILED (Count: {davydova_count})"
    print(f"Duplicate check for 'Давыдова': {status}")

if __name__ == "__main__":
    asyncio.run(main())
