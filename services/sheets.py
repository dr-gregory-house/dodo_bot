import csv
import httpx
import io
import logging

logger = logging.getLogger(__name__)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1hbvUroW0SxAbTbsn0nn-9wJyYKz-zLDJQ_PS7b83SzA/export?format=csv&gid=1833845756"

async def get_schedule(surname: str):
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(SPREADSHEET_URL)
            response.raise_for_status()
            
        # Decode content
        content = response.content.decode('utf-8')
        # print(f"DEBUG: Content length: {len(content)}") # Debug
        reader = list(csv.reader(io.StringIO(content)))
        
        if not reader or len(reader) < 2:
            print("DEBUG: Reader is empty or too short")
            return "Ошибка: Не удалось прочитать таблицу."

        # Row 0: Dates (e.g., "", "24.11", "25.11", ...)
        # Row 1: Days (e.g., "", "пн", "вт", ...)
        dates = reader[0]
        days = reader[1]
        
        # print(f"DEBUG: Dates: {dates}")
        # print(f"DEBUG: Days: {days}")
        
        schedule_lines = []
        found = False
        
        # Search for surname in Column 0 (starting from row 2)
        for row in reader[2:]:
            if not row: continue
            
            full_name = row[0]
            # Check if surname is in the full name (case-insensitive)
            if surname.lower() in full_name.lower():
                found = True
                schedule_lines.append(f"📅 График для: {full_name}")
                
                # Iterate through columns 1 to 7 (Mon-Sun)
                # Note: CSV might have more columns, but we care about the dates mapped in Row 0
                for i in range(1, len(row)):
                    if i >= len(dates): break
                    
                    shift = row[i].strip()
                    date = dates[i].strip()
                    day = days[i].strip() if i < len(days) else ""
                    
                    if shift:
                        schedule_lines.append(f"{date} ({day}): {shift}")
                break
        
        if not found:
            return f"Сотрудник с фамилией '{surname}' не найден в графике."
            
        if len(schedule_lines) == 1:
            return f"График для {surname} найден, но смен не обнаружено."
            
        return "\n".join(schedule_lines)

    except Exception as e:
        logger.error(f"Error fetching schedule: {e}")
        return "Произошла ошибка при получении графика. Попробуй позже."

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
                items.append(f"{item_name}: {quantity} лекс.")
                
        if not items:
            return "Нет заготовок на этот день/смену."
            
        title = "☀️ Утро" if is_morning else "🌙 Вечер"
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        return f"Заготовки на {days[day_index]} ({title}):\n" + "\n".join(items)

    except Exception as e:
        logger.error(f"Error fetching preps: {e}")
        return "Произошла ошибка при получении заготовок."
