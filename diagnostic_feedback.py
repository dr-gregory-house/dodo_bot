import os
import json
import logging
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    print("--- Diagnostic Report ---")
    
    # Check Time
    now = datetime.now()
    print(f"System Local Time: {now}")
    
    tz = pytz.timezone('Europe/Moscow')
    moscow_time = datetime.now(tz)
    print(f"Moscow Time: {moscow_time}")
    
    # Check Files
    feedback_file = 'data/feedback.text'
    group_file = 'data/group.json'
    
    print(f"Checking {feedback_file}...")
    if os.path.exists(feedback_file):
        print("  [OK] File exists")
        with open(feedback_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"  [OK] Content length: {len(content)}")
            if not content.strip():
                print("  [FAIL] File is empty")
    else:
        print("  [FAIL] File not found")
        print(f"  CWD: {os.getcwd()}")
        print(f"  Abs path: {os.path.abspath(feedback_file)}")

    print(f"Checking {group_file}...")
    if os.path.exists(group_file):
        print("  [OK] File exists")
        try:
            with open(group_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                group_id = data.get('group_id')
                print(f"  [OK] Group ID: {group_id}")
        except Exception as e:
            print(f"  [FAIL] Error reading JSON: {e}")
    else:
        print("  [FAIL] File not found")

if __name__ == "__main__":
    check_environment()
