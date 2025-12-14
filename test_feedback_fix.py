
import os
import sys
import time
from datetime import datetime, timedelta

# Create dummy feedback file
FEEDBACK_FILE = 'data/feedback.text'
os.makedirs('data', exist_ok=True)

def verify_logic(test_name, file_age_hours, expected_message):
    print(f"\n--- Running Test: {test_name} ---")
    
    # Create file with specific age
    now = datetime.now()
    file_time = now - timedelta(hours=file_age_hours)
    timestamp = file_time.timestamp()
    
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        f.write("Original Feedback Content")
    
    # Set modification time
    os.utime(FEEDBACK_FILE, (timestamp, timestamp))
    
    print(f"File created with mtime: {file_time}")
    
    # Simulate logic from scheduler.py
    message = None
    if os.path.exists(FEEDBACK_FILE):
        try:
            mtime = os.path.getmtime(FEEDBACK_FILE)
            file_time_check = datetime.fromtimestamp(mtime)
            
            # Check if file is older than 3 hours
            if (datetime.now() - file_time_check).total_seconds() > 3 * 3600:
                message = "На сегодня ничего нет"
                print(f"Logic Triggered: Stale file detected.")
            else:
                with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        message = content
                        print("Logic Triggered: Fresh file detected.")
        except Exception as e:
            print(f"Error: {e}")

    print(f"Result Message: '{message}'")
    if message == expected_message:
        print("✅ TEST PASSED")
    else:
        print(f"❌ TEST FAILED. Expected '{expected_message}', got '{message}'")

# Test 1: File is fresh (1 hour old)
verify_logic("Fresh File Test", 1, "Original Feedback Content")

# Test 2: File is stale (4 hours old)
verify_logic("Stale File Test", 4, "На сегодня ничего нет")

# Cleanup
if os.path.exists(FEEDBACK_FILE):
    os.remove(FEEDBACK_FILE)
