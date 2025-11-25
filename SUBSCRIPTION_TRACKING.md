# Employee Subscription Tracking Scripts

This directory contains scripts to track employee subscription status and identify who needs to subscribe to the bot.

## Scripts Overview

### 1. `not_subscribed.py`
**Purpose**: Generate a list of ALL employees from the schedule who are not subscribed to the bot.

**Output**: `data/not_subscribed.json`

**Usage**:
```bash
python3 not_subscribed.py
```

**Output Format**:
```json
[
  "Андриуца Анастасия",
  "Ашиш Шарма",
  "Бакилина Светлана",
  ...
]
```

---

### 2. `on_shift.py` ⭐ NEW
**Purpose**: Generate a list of employees who have a shift TODAY but are NOT subscribed to the bot.

**Output**: `data/on_shift.json`

**Usage**:
```bash
python3 on_shift.py
```

**Output Format**:
```json
[
  {
    "name": "Королёва Светлана",
    "role": "пиццамейкер",
    "shift": "17-23"
  },
  {
    "name": "Кузнецов Максим",
    "role": "пиццамейкер",
    "shift": "9-21"
  },
  ...
]
```

**Features**:
- ✅ Automatically gets today's date
- ✅ Fetches shifts from Google Sheets
- ✅ Cross-references with not-subscribed employees
- ✅ Sorted by role priority and name
- ✅ Includes shift time and role information

---

## Workflow

### Daily Workflow (Recommended)

Run both scripts to get complete information:

```bash
# Step 1: Update the list of all not-subscribed employees
python3 not_subscribed.py

# Step 2: Find who's on shift today and not subscribed
python3 on_shift.py
```

### Example Output

```
$ python3 on_shift.py

Checking shifts for 24.11...
Found 16 employees on shift today
Found 34 not-subscribed employees

✅ Found 7 employees on shift today who are NOT subscribed
📁 Saved to /home/anubhav/Desktop/dodo_bot/data/on_shift.json

📋 Summary:
  - Королёва Светлана (пиццамейкер) - 17-23
  - Кузнецов Максим (пиццамейкер) - 9-21
  - Павлов Павел (пиццамейкер) - 17-23
  - Ушакова Аня (пиццамейкер) - 9-17(8)
  - Андриуца Анастасия (кассир) - 9-17
  - Поспеловская Виктория (кассир) - 17-22
  - Терёхина Полина (кассир) - 17-22
```

---

## Use Cases

### 1. **Morning Reminder**
Run `on_shift.py` every morning to see which employees working today haven't subscribed yet. You can then:
- Remind them in person to subscribe
- Send a message in the work group
- Check if they need help with registration

### 2. **Weekly Report**
Run `not_subscribed.py` weekly to track overall subscription progress:
- See how many employees still need to subscribe
- Identify employees who never work (and might not need the bot)
- Track subscription adoption rate

### 3. **Shift Preparation**
Before a shift starts, check `on_shift.json` to:
- Know which employees won't receive shift notifications
- Prepare manual reminders for those employees
- Ensure critical staff (managers, mentors) are subscribed

---

## Data Files

| File | Description | Updated By |
|------|-------------|------------|
| `data/users.json` | Subscribed users (telegram_id → name) | Bot automatically |
| `data/not_subscribed.json` | All employees not subscribed | `not_subscribed.py` |
| `data/on_shift.json` | Employees on shift today who are not subscribed | `on_shift.py` |

---

## Automation Ideas

### Cron Job (Linux/Mac)
Run `on_shift.py` automatically every morning at 8 AM:

```bash
# Edit crontab
crontab -e

# Add this line:
0 8 * * * cd /home/anubhav/Desktop/dodo_bot && /home/anubhav/Desktop/dodo_bot/venv/bin/python3 on_shift.py
```

### Windows Task Scheduler
Create a scheduled task to run `on_shift.py` daily.

---

## Troubleshooting

### "No shifts found for today"
- Check if today's date exists in the Google Sheets schedule
- Verify the date format matches (DD.MM)
- Ensure the bot has access to the Google Sheets

### "not_subscribed.json not found"
- Run `not_subscribed.py` first before running `on_shift.py`

### Empty `on_shift.json`
- All employees on shift today are subscribed! 🎉
- Or no one is working today (check the schedule)

---

## Technical Details

### Dependencies
- `services/sheets.py` - For fetching schedule data
- `data/users.json` - For subscribed users list
- Google Sheets API access

### Date Format
- Input: Automatic (uses current date)
- Format: `DD.MM` (e.g., "24.11")
- Timezone: System timezone

### Role Priority (for sorting)
1. Менеджер (Manager)
2. Наставник (Mentor)
3. Инструктор (Instructor)
4. Универсал (Universal)
5. Пиццамейкер (Pizza maker)
6. Кассир (Cashier)
7. Курьер (Courier)
8. Стажёр (Trainee)

---

## Future Enhancements

- [ ] Add command-line arguments to check specific dates
- [ ] Generate weekly reports
- [ ] Send automatic reminders to not-subscribed employees
- [ ] Integration with bot commands (e.g., `/not_subscribed`)
- [ ] Export to CSV for easier sharing with managers
- [ ] Track subscription trends over time
