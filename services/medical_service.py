import json
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MEDICAL_DATA_FILE = 'data/medical_info.json'

def load_medical_data():
    if not os.path.exists(MEDICAL_DATA_FILE):
        return {"employees": []}
    try:
        with open(MEDICAL_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading medical data: {e}")
        return {"employees": []}

def save_medical_data(data):
    try:
        with open(MEDICAL_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving medical data: {e}")
        return False

def check_expiring_medical_exams():
    """
    Check for employees whose medical commission or sanitary minimum expires in <= 30 days.
    Returns a list of alerts.
    """
    data = load_medical_data()
    employees = data.get('employees', [])
    alerts = []
    
    today = datetime.now()
    warning_threshold = timedelta(days=30)
    
    for emp in employees:
        name = emp.get('name')
        if emp.get('status') == 'missing_docs':
            # Optionally alert about missing docs if needed, but user asked for expiring in 1 month
            continue
            
        # Check Med Commission
        med_date_str = emp.get('med_commission_date')
        if med_date_str:
            try:
                med_date = datetime.strptime(med_date_str, "%d.%m.%Y")
                time_left = med_date - today
                if timedelta(days=0) <= time_left <= warning_threshold:
                    alerts.append({
                        'name': name,
                        'type': 'Мед. комиссия',
                        'date': med_date_str,
                        'days_left': time_left.days
                    })
            except ValueError:
                logger.error(f"Invalid date format for {name}: {med_date_str}")

        # Check San Min
        san_date_str = emp.get('san_min_date')
        if san_date_str:
            try:
                san_date = datetime.strptime(san_date_str, "%d.%m.%Y")
                time_left = san_date - today
                if timedelta(days=0) <= time_left <= warning_threshold:
                    alerts.append({
                        'name': name,
                        'type': 'Сан. минимум',
                        'date': san_date_str,
                        'days_left': time_left.days
                    })
            except ValueError:
                logger.error(f"Invalid date format for {name}: {san_date_str}")
                
    return alerts

def update_employee_medical_info(surname, med_date=None, san_date=None):
    """
    Update medical info for an employee.
    """
    data = load_medical_data()
    employees = data.get('employees', [])
    updated = False
    
    for emp in employees:
        if surname.lower() in emp['name'].lower():
            if med_date:
                emp['med_commission_date'] = med_date
                if 'status' in emp and emp['status'] == 'missing_docs':
                    del emp['status'] # Remove missing flag if updated
            if san_date:
                emp['san_min_date'] = san_date
                if 'status' in emp and emp['status'] == 'missing_docs':
                    del emp['status']
            updated = True
            break
            
    if updated:
        save_medical_data(data)
        return True
    return False

def get_all_medical_issues():
    """
    Get a list of all medical issues (expired, expiring soon, missing docs).
    Returns list of dicts: {'name': str, 'issue': str, 'details': str}
    """
    data = load_medical_data()
    employees = data.get('employees', [])
    issues = []
    
    today = datetime.now()
    warning_threshold = timedelta(days=30)
    
    for emp in employees:
        name = emp.get('name')
        
        # 1. Missing Docs
        if emp.get('status') == 'missing_docs':
            issues.append({
                'name': name,
                'issue': 'Нет документов',
                'details': 'Необходимо принести мед. книжку'
            })
            continue
            
        # 2. Check Med Commission
        med_date_str = emp.get('med_commission_date')
        if med_date_str:
            try:
                med_date = datetime.strptime(med_date_str, "%d.%m.%Y")
                time_left = med_date - today
                days = time_left.days
                
                if days < 0:
                    issues.append({
                        'name': name,
                        'issue': 'Мед. комиссия (Просрочено)',
                        'details': f"Истекла {med_date_str} ({abs(days)} дн. назад)"
                    })
                elif days <= 30:
                    issues.append({
                        'name': name,
                        'issue': 'Мед. комиссия (Истекает)',
                        'details': f"Истекает {med_date_str} (осталось {days} дн.)"
                    })
            except ValueError:
                pass

        # 3. Check San Min
        san_date_str = emp.get('san_min_date')
        if san_date_str:
            try:
                san_date = datetime.strptime(san_date_str, "%d.%m.%Y")
                time_left = san_date - today
                days = time_left.days
                
                if days < 0:
                    issues.append({
                        'name': name,
                        'issue': 'Сан. минимум (Просрочено)',
                        'details': f"Истек {san_date_str} ({abs(days)} дн. назад)"
                    })
                elif days <= 30:
                    issues.append({
                        'name': name,
                        'issue': 'Сан. минимум (Истекает)',
                        'details': f"Истекает {san_date_str} (осталось {days} дн.)"
                    })
            except ValueError:
                pass
                
    return issues

def get_employee_status(surname):
    data = load_medical_data()
    for emp in data.get('employees', []):
        if surname.lower() in emp['name'].lower():
            return emp
    return None

def is_manager(surname):
    """
    Check if the employee with the given surname has the 'manager' role.
    """
    data = load_medical_data()
    for emp in data.get('employees', []):
        if surname.lower() in emp['name'].lower():
            return emp.get('role') == 'manager'
    return False
