#!/usr/bin/env python3
"""
Verification script for cashier items in preps
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sheets import get_preps

async def test_cashier_items():
    print("Testing cashier items in morning preps...")
    print("=" * 60)
    
    # Test Monday morning (day_index=0, is_morning=True)
    result = await get_preps(day_index=0, is_morning=True)
    print("\n📅 Понедельник - Утро:")
    print(result)
    print("\n" + "=" * 60)
    
    # Check if cashier items are present
    if "На кассу" in result and "должны быть до 10 часов" in result:
        print("\n✅ SUCCESS: Cashier items section found!")
        if "Салат Цезарь" in result and "9 шт" in result:
            print("✅ Caesar Salad (9 pcs) - Found")
        if "Салат овощной" in result and "3 шт" in result:
            print("✅ Vegetable Salad (3 pcs) - Found")
        if "Чикен ролл" in result and "10 шт" in result:
            print("✅ Chicken Roll (10 pcs) - Found")
    else:
        print("\n❌ ERROR: Cashier items section NOT found!")
        return False
    
    # Test that cashier items are NOT in evening preps
    print("\n" + "=" * 60)
    print("\nTesting that cashier items are NOT in evening preps...")
    result_evening = await get_preps(day_index=0, is_morning=False)
    print("\n📅 Понедельник - Вечер:")
    print(result_evening)
    print("\n" + "=" * 60)
    
    if "На кассу" not in result_evening:
        print("\n✅ SUCCESS: Cashier items correctly excluded from evening preps!")
    else:
        print("\n⚠️  WARNING: Cashier items found in evening preps (should only be in morning)")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_cashier_items())
