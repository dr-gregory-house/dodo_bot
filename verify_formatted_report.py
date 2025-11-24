from services.medical_service import get_all_medical_issues
import logging

logging.basicConfig(level=logging.INFO)

def test_formatted_report():
    print("--- Testing Formatted Report Logic ---")
    
    issues = get_all_medical_issues()
    
    red_list = []
    yellow_list = []
    
    for item in issues:
        if "Просрочено" in item['issue'] or "Нет документов" in item['issue']:
            red_list.append(item)
        else:
            yellow_list.append(item)
            
    print("📋 **Отчет по медицинским документам**\n")
    
    if red_list:
        print("🔴 **Просрочено / Нет документов**")
        for item in red_list:
            if "Нет документов" in item['issue']:
                print(f"• {item['name']} (Нет документов)")
            else:
                print(f"• {item['name']} ({item['issue']}: {item['details']})")
        print("")
        
    if yellow_list:
        print("🟡 **Истекает в ближайшее время**")
        for item in yellow_list:
            print(f"• {item['name']} ({item['issue']}: {item['details']})")

if __name__ == "__main__":
    test_formatted_report()
