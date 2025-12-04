import pytz
from datetime import time, datetime, timedelta

tz = pytz.timezone('Europe/Moscow')
t = time(8, 55, tzinfo=tz)
print(f"Time object: {t}")
print(f"Tzinfo: {t.tzinfo}")

# Check how it behaves when attached to a date
now = datetime.now()
dt = datetime.combine(now.date(), t)
print(f"Combined datetime: {dt}")
print(f"Offset: {dt.utcoffset()}")

# Compare with ZoneInfo
try:
    from zoneinfo import ZoneInfo
    zi = ZoneInfo('Europe/Moscow')
    t_zi = time(8, 55, tzinfo=zi)
    print(f"ZoneInfo time: {t_zi}")
    dt_zi = datetime.combine(now.date(), t_zi)
    print(f"ZoneInfo combined: {dt_zi}")
    print(f"ZoneInfo offset: {dt_zi.utcoffset()}")
except ImportError:
    print("ZoneInfo not available")
