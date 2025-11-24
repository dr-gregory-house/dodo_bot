import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from services.sheets import get_preps

async def verify():
    print("Verifying Morning Preps (Monday)...")
    morning_preps = await get_preps(0, True)
    
    # Check for Canned Goods
    if "🥫 **Консервы:**" in morning_preps:
        print("✅ Canned Goods section found.")
    else:
        print("❌ Canned Goods section MISSING.")
        
    if "Ананасы" in morning_preps and "Халапеньо" in morning_preps and "Огурцы" in morning_preps:
        print("✅ Canned items found.")
    else:
        print("❌ Canned items MISSING.")

    # Check for Seafood
    if "🦐 **Морепродукты:**" in morning_preps:
        print("✅ Seafood section found.")
    else:
        print("❌ Seafood section MISSING.")
        
    if "Креветки" in morning_preps:
        print("✅ Seafood items found.")
    else:
        print("❌ Seafood items MISSING.")

    # Check for Pork Neck
    if "Свиная шейка" in morning_preps:
        print("✅ Pork Neck found in Morning.")
    else:
        print("❌ Pork Neck MISSING in Morning.")

    print("\nVerifying Evening Preps (Monday)...")
    evening_preps = await get_preps(0, False)
    
    # Check that Canned/Seafood are NOT present
    if "🥫 **Консервы:**" not in evening_preps and "🦐 **Морепродукты:**" not in evening_preps:
        print("✅ Canned/Seafood correctly ABSENT in Evening.")
    else:
        print("❌ Canned/Seafood FOUND in Evening (Should not be there).")

    # Check for Pork Neck in Evening
    if "Свиная шейка" in evening_preps:
        print("✅ Pork Neck found in Evening.")
    else:
        print("❌ Pork Neck MISSING in Evening.")

if __name__ == "__main__":
    asyncio.run(verify())
