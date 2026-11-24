from datetime import datetime
from app.models.stats import DayOfWeekEnum

# In Python: Monday is 0 and Sunday is 6
_WEEKDAY_MAP = {
    6: DayOfWeekEnum.SUNDAY.value,
    0: DayOfWeekEnum.MONDAY.value,
    1: DayOfWeekEnum.TUESDAY.value,
    2: DayOfWeekEnum.WEDNESDAY.value,
    3: DayOfWeekEnum.THURSDAY.value,
    4: DayOfWeekEnum.FRIDAY.value,
    5: DayOfWeekEnum.SATURDAY.value,
}

def get_day_of_week(dt: datetime) -> str:
    """
    Returns the standardized day of week string (sunday..saturday) for a given datetime.
    """
    return _WEEKDAY_MAP[dt.weekday()]

def is_arrival_on_time(entry_time: datetime, event_start_time: datetime, grace_period_minutes: int = 15) -> bool:
    """
    Determines if participant arrived on time or early (up to grace_period_minutes after event start).
    """
    delta_seconds = (entry_time - event_start_time).total_seconds()
    # Arrival anytime before start, or up to grace_period_minutes after
    return delta_seconds <= (grace_period_minutes * 60)
