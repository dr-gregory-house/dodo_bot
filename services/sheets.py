import csv
import httpx
import io
import logging

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
    """Calculate hours from shift time like '9-17' or '09:00-17:00'"""
    try:
        # Remove spaces and split on dash
        shift_time = shift_time.replace(' ', '').replace(':', '')
        parts = shift_time.split('-')
        if len(parts) != 2:
            return 0
        
        # Parse start and end times
        start = int(parts[0]) if len(parts[0]) <= 2 else int(parts[0][:2])
        end = int(parts[1]) if len(parts[1]) <= 2 else int(parts[1][:2])
        
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

async def get_schedule(surname: str):
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(SPREADSHEET_URL)
            response.raise_for_status()
            
        # Decode content
        content = response.content.decode('utf-8')
        reader = list(csv.reader(io.StringIO(content)))
        
        if not reader or len(reader) < 2:
            return "Ошибка: Не удалось прочитать таблицу."

        # Row 0: Dates (e.g., "", "24.11", "25.11", ...)
        # Row 1: Days (e.g., "", "пн", "вт", ...)
        dates = reader[0]
        days = reader[1]
        
        schedule_lines = []
        found = False
        shifts = []
        current_role = None  # Track the current role section
        
        # Search for surname in Column 0 (starting from row 2)
        for row in reader[2:]:
            if not row: continue
            
            full_name = row[0].strip()
            
            # Stop processing if we reach "Мойка:" section or beyond
            if 'мойка' in full_name.lower() or full_name.lower() in ['ольга', 'екатерина', 'наталья']:
                break
            
            # Check if this row is a role header
            detected_role = detect_role_header(full_name)
            if detected_role:
                current_role = detected_role
                continue  # Skip to next row
            
            # Check if surname is in the full name (case-insensitive)
            if surname.lower() in full_name.lower():
                found = True
                hourly_rate = get_hourly_rate_by_role(current_role)
                total_hours = 0
                total_payment = 0
                
                # Iterate through columns to find shifts
                for i in range(1, len(row)):
                    if i >= len(dates): break
                    
                    shift = row[i].strip()
                    date = dates[i].strip()
                    day = days[i].strip() if i < len(days) else ""
                    
                    if shift:
                        hours = calculate_shift_hours(shift)
                        payment = hours * hourly_rate
                        total_hours += hours
                        total_payment += payment
                        
                        # Map day abbreviation to full name
                        day_map = {
                            'пн': 'Понедельник',
                            'вт': 'Вторник',
                            'ср': 'Среда',
                            'чт': 'Четверг',
                            'пт': 'Пятница',
                            'сб': 'Суббота',
                            'вс': 'Воскресенье'
                        }
                        day_full = day_map.get(day.lower(), day)
                        
                        shifts.append(f"• {day_full}, {date} — {shift}")
                
                # Build header
                role_display = current_role.capitalize() if current_role else "Не указана"
                schedule_lines.append(f"🗓 **График работы**\n👤 {full_name}\n💼 Роль: {role_display}\n")
                if total_hours > 0:
                    schedule_lines.append(f"⏱ Общие часы за неделю: {int(total_hours)} часов")
                    schedule_lines.append(f"💵 Ставка: {hourly_rate}₽/час")
                    schedule_lines.append(f"💰 Оплата за неделю: {int(total_payment):,}₽ (Без учета надбавки за стажа)\n".replace(',', ' '))
                
                # Add shifts
                schedule_lines.extend(shifts)
                break
        
        if not found:
            return f"Сотрудник с фамилией '{surname}' не найден в графике."
            
        if len(schedule_lines) == 1:
            return f"График для {surname} найден, но смен не обнаружено."
            
        return "\n".join(schedule_lines)

    except Exception as e:
        logger.error(f"Error fetching schedule: {e}")
        return "Произошла ошибка при получении графика. Попробуй позже."

async def get_who_on_shift(target_date: str, surname: str = None):
    """
    Get all employees working on a specific date, grouped by role
    target_date: format "DD.MM" e.g. "24.11"
    surname: optional, to show the user's shift time in the header
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(SPREADSHEET_URL)
            response.raise_for_status()
            
        content = response.content.decode('utf-8')
        reader = list(csv.reader(io.StringIO(content)))
        
        if not reader or len(reader) < 2:
            return "Ошибка: Не удалось прочитать таблицу."

        dates = reader[0]
        days = reader[1]
        
        # Find the column index for the target date
        target_col = None
        target_day = None
        actual_date = None
        
        # First, try to find the exact date
        for i, date in enumerate(dates):
            date_stripped = date.strip()
            if date_stripped == target_date:
                target_col = i
                target_day = days[i].strip() if i < len(days) else ""
                actual_date = date_stripped
                break
        
        # If not found, find the next available date
        if target_col is None:
            from datetime import datetime
            try:
                target_dt = datetime.strptime(f"{target_date}.2025", "%d.%m.%Y")
                
                for i, date in enumerate(dates):
                    date_stripped = date.strip()
                    if date_stripped and '.' in date_stripped:
                        try:
                            schedule_dt = datetime.strptime(f"{date_stripped}.2025", "%d.%m.%Y")
                            if schedule_dt >= target_dt:
                                target_col = i
                                target_day = days[i].strip() if i < len(days) else ""
                                actual_date = date_stripped
                                break
                        except:
                            continue
            except:
                pass
        
        if target_col is None:
            return f"Дата {target_date} не найдена в графике, и нет доступных будущих смен."
        
        # Collect employees by role
        employees_by_role = {}
        current_role = None
        user_shift_time = None
        total_count = 0
        
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
                if current_role not in employees_by_role:
                    employees_by_role[current_role] = []
                continue
            
            # Check if employee has a shift on this date
            if target_col < len(row):
                shift = row[target_col].strip()
                if shift:
                    total_count += 1
                    role_display = current_role.capitalize() if current_role else "Неизвестно"
                    
                    # Add to role group
                    if current_role and current_role in employees_by_role:
                        employees_by_role[current_role].append(f"👤 {full_name} ({shift})")
                    
                    # Check if this is the user
                    if surname and surname.lower() in full_name.lower():
                        user_shift_time = shift
        
        if total_count == 0:
            return f"На {actual_date} нет смен в графике."
        
        # Build output
        lines = []
        
        # Show if we're displaying a different date than requested
        if actual_date != target_date:
            lines.append(f"ℹ️ Дата {target_date} не найдена. Показываю ближайшую дату:\n")
        
        # Header with user's shift if found
        if user_shift_time:
            lines.append(f"🕐 Твоя смена сегодня: {user_shift_time}")
        lines.append(f"📅 Дата: {actual_date}")
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

async def get_preps(day_index: int, is_morning: bool):
    """
    day_index: 0=Mon, 1=Tue, ..., 6=Sun
    is_morning: True for Morning, False for Evening
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(PREPS_URL)
            response.raise_for_status()
            
        content = response.content.decode('utf-8')
        reader = list(csv.reader(io.StringIO(content)))
        
        if not reader or len(reader) < 15:
            return "Ошибка: Не удалось прочитать таблицу заготовок."

        # Define rows based on Morning/Evening
        # Morning: Rows 2-8 (indices 2-8)
        # Evening: Rows 10-16 (indices 10-16)
        start_row = 2 if is_morning else 10
        end_row = 9 if is_morning else 17
        
        # Column mapping: Mon=0, Tue=2, Wed=4, Thu=6, Fri=8, Sat=10, Sun=12
        col_idx = day_index * 2
        
        items = []
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
                items.append(f"**{item_name}**: `{quantity}` лекс.")
                
        if not items:
            return "Нет заготовок на этот день/смену."
            
        title = "☀️ Утро" if is_morning else "🌙 Вечер"
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        
        header = f"🔪 **Заготовки на {days[day_index]}** ({title})\n━━━━━━━━━━━━\n"
        body = "\n".join([f"• {item}" for item in items])
        
        return header + body

    except Exception as e:
        logger.error(f"Error fetching preps: {e}")
        return "Произошла ошибка при получении заготовок."
