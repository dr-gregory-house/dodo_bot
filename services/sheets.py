import csv
import io
import logging
import urllib.request
from datetime import datetime
from services.sheet_manager import sheet_manager

logger = logging.getLogger(__name__)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1hbvUroW0SxAbTbsn0nn-9wJyYKz-zLDJQ_PS7b83SzA/export?format=csv&gid=1833845756"

# Hourly rates from wages system
HOURLY_RATES = {
    'стажёр': 130,
    'пиццамейкер': 205,
    'кассир': 205,
    'универсал': 225,
    'инструктор': 225,
    'наставник': 230,
    'менеджер': 255,
}

def calculate_shift_hours(shift_time: str) -> float:
    """Calculate hours from shift time like '9-17', '09:00-17:00', or '9-21(p)'"""
    try:
        # Remove spaces and colons
        shift_time = shift_time.replace(' ', '').replace(':', '')
        
        # Split on dash
        parts = shift_time.split('-')
        if len(parts) != 2:
            return 0
        
        # Extract only numeric characters from each part (handles annotations like (p), (д), etc.)
        start_str = ''.join(c for c in parts[0] if c.isdigit())
        end_str = ''.join(c for c in parts[1] if c.isdigit())
        
        if not start_str or not end_str:
            return 0
        
        # Parse start and end times (take first 2 digits for times like 0900)
        start = int(start_str) if len(start_str) <= 2 else int(start_str[:2])
        end = int(end_str) if len(end_str) <= 2 else int(end_str[:2])
        
        # Calculate duration
        hours = end - start
        if hours < 0:  # Handle overnight shifts
            hours += 24
        
        return hours
    except:
        return 0

def get_hourly_rate_by_role(role: str) -> int:
    """Get hourly rate based on role"""
    if not role:
        return 205  # Default to Pizzamaker rate
    
    role_lower = role.lower()
    for role_key, rate in HOURLY_RATES.items():
        if role_key in role_lower:
            return rate
    # Default to Pizzamaker rate if no role match
    return 205

def detect_role_header(row_text: str) -> str | None:
    """Detect if a row is a role header and return the role name"""
    if not row_text:
        return None
    
    row_lower = row_text.lower().strip()
    
    # Role headers mapping
    role_headers = {
        'менеджер': 'менеджер',
        'наставник': 'наставник',
        'инструктор': 'инструктор',
        'универсал': 'универсал',
        'кассир': 'кассир',
        'пиццамейкер': 'пиццамейкер',
        'стажёр': 'стажёр',
        'стажер': 'стажёр',
    }
    
    for header_key, role in role_headers.items():
        if header_key in row_lower:
            return role
    
    return None

from services.sheet_manager import sheet_manager

import urllib.request

async def get_schedule(surname: str):
    if not surname:
        return []

    # Hardcoded redirect for Булатова to view manager schedule
    if 'булатова' in surname.lower():
        surname = 'Ахмитенко'

    try:
        # Get all relevant sheets
        sheets = await sheet_manager.get_sheets()
        if not sheets:
            return []
            
        schedules = []
        
        for sheet in sheets:
            gid = sheet['gid']
            sheet_name = sheet['name']
            
            url = f"https://docs.google.com/spreadsheets/d/1hbvUroW0SxAbTbsn0nn-9wJyYKz-zLDJQ_PS7b83SzA/export?format=csv&gid={gid}"
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                
                reader = list(csv.reader(io.StringIO(content)))
                
                if not reader or len(reader) < 2:
                    continue

                dates = reader[0]
                days = reader[1]
                
                # Parse start date from the first date column (index 1)
                start_date_dt = datetime.min
                if len(dates) > 1:
                    try:
                        # Date format is DD.MM
                        # We assume current year or next year
                        date_str = dates[1].strip()
                        if date_str:
                            # Add year. If it's late in the year and date is Jan, it's next year.
                            now = datetime.now()
                            dt = datetime.strptime(f"{date_str}.{now.year}", "%d.%m.%Y")
                            
                            # Heuristic for year transition:
                            # If current month is Nov/Dec and sheet date is Jan/Feb, add 1 year.
                            # If current month is Jan/Feb and sheet date is Nov/Dec, subtract 1 year.
                            if now.month >= 11 and dt.month <= 2:
                                dt = dt.replace(year=now.year + 1)
                            elif now.month <= 2 and dt.month >= 11:
                                dt = dt.replace(year=now.year - 1)
                                
                            start_date_dt = dt
                    except:
                        pass
                
                current_role = None
                
                for row in reader[2:]:
                    if not row: continue
                    
                    full_name = row[0].strip()
                    
                    if 'мойка' in full_name.lower() or full_name.lower() in ['ольга', 'екатерина', 'наталья']:
                        break
                    
                    detected_role = detect_role_header(full_name)
                    if detected_role:
                        current_role = detected_role
                        continue
                    
                    if surname.lower() in full_name.lower():
                        hourly_rate = get_hourly_rate_by_role(current_role)
                        
                        shifts = []
                        total_hours = 0
                        total_payment = 0
                        
                        for i in range(1, len(row)):
                            if i >= len(dates): break
                            
                            shift = row[i].strip()
                            date = dates[i].strip()
                            day = days[i].strip() if i < len(days) else ""
                            
                            if shift:
                                hours = calculate_shift_hours(shift)
                                
                                # Only include valid shifts with actual dates and hours > 0
                                if date and hours > 0:
                                    payment = hours * hourly_rate
                                    total_hours += hours
                                    total_payment += payment
                                    
                                    day_map = {
                                        'пн': 'Понедельник', 'вт': 'Вторник', 'ср': 'Среда',
                                        'чт': 'Четверг', 'пт': 'Пятница', 'сб': 'Суббота', 'вс': 'Воскресенье'
                                    }
                                    day_full = day_map.get(day.lower(), day)
                                    
                                    shifts.append(f"• {day_full}, {date} — {shift}")
                        
                        if shifts:
                            role_display = current_role.capitalize() if current_role else "Не указана"
                            
                            # Extract date range from sheet name if possible, else use sheet name
                            # Sheet names: "Кухня 17 - 23", "кухня 24-30"
                            # We want "17 - 23" or "17.11 — 23.11" if we can guess month
                            # Let's stick to the sheet name numbers for now but clean it up
                            
                            clean_sheet_name = sheet_name.replace('кухня', '').replace('Кухня', '').strip()
                            # Remove trailing dots or chars
                            clean_sheet_name = clean_sheet_name.strip('.')
                            
                            header = f"🗓 <b>График работы</b> ({clean_sheet_name})\n👤 <b>{full_name}</b>\n💼 {role_display}\n"
                            
                            stats = ""
                            if total_hours > 0:
                                stats += f"📊 <b>Итоги недели:</b>\n"
                                stats += f"⏱ {int(total_hours)} часов  |  💰 {int(total_payment):,}₽ (без учёта надбавки за стаж)\n".replace(',', ' ')
                            
                            shifts_text = "\n📋 <b>Смены:</b>\n"
                            for shift_item in shifts:
                                # shift_item is "• Понедельник, 17.11 — 9-23"
                                # We want "🔹 Пн, 17.11: 9-23 (14ч)"
                                
                                # Parse the existing format
                                # "• DayFull, Date — Shift"
                                try:
                                    parts = shift_item.split('—')
                                    left = parts[0].replace('•', '').strip() # "Понедельник, 17.11"
                                    shift_time = parts[1].strip() # "9-23"
                                    
                                    day_date = left.split(',')
                                    day_full = day_date[0].strip()
                                    date_short = day_date[1].strip()
                                    
                                    # Shorten day
                                    day_map_short = {
                                        'Понедельник': 'Пн', 'Вторник': 'Вт', 'Среда': 'Ср',
                                        'Четверг': 'Чт', 'Пятница': 'Пт', 'Суббота': 'Сб', 'Воскресенье': 'Вс'
                                    }
                                    day_short = day_map_short.get(day_full, day_full[:2])
                                    
                                    # Calculate duration again for display
                                    duration = calculate_shift_hours(shift_time)
                                    
                                    shifts_text += f"🔹 {day_short}, {date_short}: {shift_time} ({int(duration)}ч)\n"
                                except:
                                    shifts_text += f"{shift_item}\n"
                            
                            text = header + "\n" + stats + shifts_text
                            
                            schedules.append({
                                'text': text,
                                'start_date': start_date_dt,
                                'sheet_name': sheet_name
                            })
                        break
                        
            except Exception as e:
                logger.error(f"Error processing sheet {sheet_name}: {e}")
                continue
        
        # Sort schedules by date
        schedules.sort(key=lambda x: x['start_date'])
        
        return schedules

    except Exception as e:
        logger.error(f"Error fetching schedule: {e}")
        return []

async def get_shifts_for_date(target_date: str):
    """
    Get all shifts for a specific date.
    Returns a list of dicts: {'name': str, 'role': str, 'shift': str}
    """
    try:
        sheets = await sheet_manager.get_sheets()
        if not sheets:
            return []
            
        target_sheet_content = None
        actual_date = None
        
        for sheet in sheets:
            gid = sheet['gid']
            url = f"https://docs.google.com/spreadsheets/d/1hbvUroW0SxAbTbsn0nn-9wJyYKz-zLDJQ_PS7b83SzA/export?format=csv&gid={gid}"
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                
                reader = list(csv.reader(io.StringIO(content)))
                
                if not reader or len(reader) < 2:
                    continue
                    
                dates = reader[0]
                
                # Check if target_date is in this sheet
                if target_date in [d.strip() for d in dates]:
                    target_sheet_content = reader
                    actual_date = target_date
                    break
            except:
                continue
        
        if not target_sheet_content:
             return []

        reader = target_sheet_content
        dates = reader[0]
        
        # Find column index
        target_col = -1
        for i, date in enumerate(dates):
            if date.strip() == actual_date:
                target_col = i
                break
                
        if target_col == -1:
            return []

        # Collect employees
        shifts_data = []
        current_role = None
        
        for row in reader[2:]:
            if not row: continue
            
            full_name = row[0].strip()
            
            # Stop at Мойка section
            if 'мойка' in full_name.lower() or full_name.lower() in ['ольга', 'екатерина', 'наталья']:
                break
            
            # Check if this is a role header
            detected_role = detect_role_header(full_name)
            if detected_role:
                current_role = detected_role
                continue
            
            # Check if employee has a shift on this date
            if target_col < len(row):
                shift = row[target_col].strip()
                if shift:
                    shifts_data.append({
                        'name': full_name,
                        'role': current_role,
                        'shift': shift
                    })
        
        return shifts_data

    except Exception as e:
        logger.error(f"Error fetching shifts for date: {e}")
        return []

async def get_who_on_shift(target_date: str, surname: str = None):
    """
    Get all employees working on a specific date, grouped by role
    target_date: format "DD.MM" e.g. "24.11"
    surname: optional, to show the user's shift time in the header
    """
    try:
        shifts_data = await get_shifts_for_date(target_date)
        
        if not shifts_data:
             return f"На {target_date} нет смен в графике или график не найден."

        # Group by role
        employees_by_role = {}
        user_shift_time = None
        total_count = len(shifts_data)
        
        for item in shifts_data:
            role = item['role']
            name = item['name']
            shift = item['shift']
            
            if role:
                if role not in employees_by_role:
                    employees_by_role[role] = []
                employees_by_role[role].append(f"👤 {name} ({shift})")
            
            if surname and surname.lower() in name.lower():
                user_shift_time = shift
        
        # Build output
        lines = []
        
        # Header with user's shift if found
        if user_shift_time:
            lines.append(f"🕐 Твоя смена сегодня: {user_shift_time}")
        lines.append(f"📅 Дата: {target_date}")
        lines.append(f"👥 Коллеги на смене: {total_count} человек(а)\n")
        
        # Role groups
        role_names = {
            'менеджер': 'Менеджеры',
            'наставник': 'Наставники',
            'инструктор': 'Инструктора',
            'универсал': 'Универсалы',
            'кассир': 'Кассиры',
            'пиццамейкер': 'Пиццамейкеры',
            'стажёр': 'Стажёры'
        }
        
        for role, employees in employees_by_role.items():
            if employees:
                role_display = role_names.get(role, role.capitalize())
                lines.append(f"👥 {role_display}:")
                lines.extend(employees)
                lines.append("")  # Empty line between roles
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error fetching who's on shift: {e}")
        return "Произошла ошибка при получении данных о смене."

PREPS_URL = "https://docs.google.com/spreadsheets/d/1TdoxhVu3l2blTtpf_ekoIESR7MYQDxs1/export?format=csv&gid=1242464660"



def load_preps_config():
    try:
        import json
        import os
        # Use absolute path relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, 'data', 'preps_config.json')
        if not os.path.exists(config_path):
            return None
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading preps config: {e}")
        return None

async def get_preps(day_index: int, is_morning: bool):
    """
    day_index: 0=Mon, 1=Tue, ..., 6=Sun
    is_morning: True for Morning, False for Evening
    """
    try:
        # 1. Fetch Vegetables from Sheet (Existing Logic)
        import urllib.request
        req = urllib.request.Request(PREPS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            
        reader = list(csv.reader(io.StringIO(content)))
        
        items = []
        
        if reader and len(reader) >= 15:
            # Define rows based on Morning/Evening
            # Morning: Rows 2-8 (indices 2-8)
            # Evening: Rows 10-16 (indices 10-16)
            start_row = 2 if is_morning else 10
            end_row = 9 if is_morning else 17
            
            # Column mapping: Mon=0, Tue=2, Wed=4, Thu=6, Fri=8, Sat=10, Sun=12
            col_idx = day_index * 2
            
            items.append("🥦 **Овощи:**")
            
            chicken_fillet_item = None
            
            for i in range(start_row, end_row):
                if i >= len(reader): break
                row = reader[i]
                if len(row) <= col_idx + 1: continue
                
                item_name = row[col_idx].strip()
                quantity = row[col_idx + 1].strip()
                
                # Skip header rows or empty items
                if not item_name or "Дни недели" in item_name or "Кол-во" in item_name:
                    continue
                
                if item_name and quantity:
                    # Check for Chicken Fillet to move to Meat
                    if "филе курицы" in item_name.lower() or "цыпленок" in item_name.lower():
                        chicken_fillet_item = f"• {item_name}: `{quantity}` лекс."
                    else:
                        items.append(f"• {item_name}: `{quantity}` лекс.")
        else:
            items.append("⚠️ Не удалось загрузить овощи из таблицы.")

        # 2. Load Meat and Sauces from JSON
        config = load_preps_config()
        if config:
            # Meat Schedule
            meat_schedule = config.get('meat_schedule', {})
            day_key = str(day_index)
            if day_key in meat_schedule:
                time_key = "morning" if is_morning else "evening"
                meat_items = meat_schedule[day_key].get(time_key, [])
                
                if meat_items:
                    # Separate Feta (Брынза) to add to Vegetables
                    feta_item = None
                    filtered_meat_items = []
                    for item in meat_items:
                        if "брынза" in item['name'].lower():
                            feta_item = item
                        else:
                            filtered_meat_items.append(item)
                    
                    # Add Feta to Vegetables section (if Vegetables section exists)
                    if feta_item:
                        # If we have vegetables from sheet, append Feta there
                        # If not, we might need to create the header
                        if not items or "🥦 **Овощи:**" not in items[0]:
                             items.insert(0, "🥦 **Овощи:**")
                        
                        items.append(f"• {feta_item['name']}: `{feta_item['quantity']}`")

                    if filtered_meat_items or chicken_fillet_item:
                        items.append("\n🥩 **Мясо:**")
                        if chicken_fillet_item:
                             items.append(chicken_fillet_item)
                        for item in filtered_meat_items:
                            items.append(f"• {item['name']}: `{item['quantity']}`")
            
            # Canned Goods (Morning only)
            if is_morning:
                canned_schedule = config.get('canned_schedule', {})
                if day_key in canned_schedule:
                    canned_items = canned_schedule[day_key].get('morning', [])
                    if canned_items:
                        items.append("\n🥫 **Консервы:**")
                        for item in canned_items:
                            items.append(f"• {item['name']}: `{item['quantity']}`")

            # Seafood (Morning only)
            if is_morning:
                seafood_schedule = config.get('seafood_schedule', {})
                if day_key in seafood_schedule:
                    seafood_items = seafood_schedule[day_key].get('morning', [])
                    if seafood_items:
                        items.append("\n🦐 **Морепродукты:**")
                        for item in seafood_items:
                            items.append(f"• {item['name']}: `{item['quantity']}`")

            # Cashier Items (Morning only - daily items for cashier station)
            if is_morning:
                cashier_items = config.get('cashier_items', [])
                if cashier_items:
                    items.append("\n🧾 **На кассу (должны быть до 10 часов!):**")
                    for item in cashier_items:
                        items.append(f"• {item['name']}: `{item['quantity']}`")


            # Sauces (Evening only)
            if not is_morning:
                sauces = config.get('sauces', [])
                if sauces:
                    items.append("\n🥣 **Соуса:**")
                    for sauce in sauces:
                        items.append(f"• {sauce['name']}: `{sauce['quantity']}`")
        
        if not items:
            return "Нет заготовок на этот день/смену."
            
        title = "☀️ Утро" if is_morning else "🌙 Вечер"
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        
        header = f"🔪 **Заготовки на {days[day_index]}** ({title})\n━━━━━━━━━━━━\n"
        body = "\n".join(items)
        
        return header + body

    except Exception as e:
        logger.error(f"Error fetching preps: {e}")
        return "Произошла ошибка при получении заготовок."

async def get_all_employees():
    """
    Get a list of all unique employee names from the schedule.
    """
    try:
        # Load config
        import json
        import os
        # Use absolute path relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, 'data', 'employees_config.json')
        blacklist = []
        aliases = {}
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    blacklist = [name.lower() for name in config.get('blacklist', [])]
                    # Flatten aliases for reverse lookup: "Variant" -> "Canonical"
                    for canonical, variants in config.get('aliases', {}).items():
                        for variant in variants:
                            aliases[variant.lower()] = canonical
            except Exception as e:
                logger.error(f"Error loading employees config: {e}")

        sheets = await sheet_manager.get_sheets()
        if not sheets:
            return []
            
        employees = set()
        
        # Manual additions (Admins/Managers not in schedule)
        MANUAL_EMPLOYEES = ["Лилия Смолкина", "Холодный цех"]
        for manual_emp in MANUAL_EMPLOYEES:
            employees.add(manual_emp)
        
        for sheet in sheets:
            gid = sheet['gid']
            url = f"https://docs.google.com/spreadsheets/d/1hbvUroW0SxAbTbsn0nn-9wJyYKz-zLDJQ_PS7b83SzA/export?format=csv&gid={gid}"
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                
                reader = list(csv.reader(io.StringIO(content)))
                
                if not reader or len(reader) < 2:
                    continue
                
                for row in reader[2:]:
                    if not row: continue
                    
                    full_name = row[0].strip()
                    
                    # Skip empty or specific non-employee rows
                    if not full_name: continue
                    if 'мойка' in full_name.lower(): break # Stop at Moyka
                    if full_name.lower() in ['ольга', 'екатерина', 'наталья']: break 
                    
                    if detect_role_header(full_name):
                        continue
                        
                    # Also skip if it looks like a date or empty
                    if len(full_name) < 2: continue
                    
                    # Normalization
                    # 1. Replace multiple spaces with single space
                    normalized_name = ' '.join(full_name.split())
                    
                    # 2. Check blacklist
                    is_blacklisted = False
                    for black_name in blacklist:
                        if black_name in normalized_name.lower():
                            is_blacklisted = True
                            break
                    if is_blacklisted:
                        continue
                        
                    # 3. Handle aliases/duplicates
                    # Check if this name is an alias for something else
                    if normalized_name.lower() in aliases:
                        normalized_name = aliases[normalized_name.lower()]
                    
                    employees.add(normalized_name)
                    
            except Exception as e:
                logger.error(f"Error processing sheet for employees: {e}")
                continue
                
        return sorted(list(employees))
        
    except Exception as e:
        logger.error(f"Error fetching all employees: {e}")
        return []
