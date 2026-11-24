import pytest
from datetime import datetime
from app.classification.temporal_features import get_day_of_week, is_arrival_on_time

def test_get_day_of_week():
    # 2026-11-22 is Sunday
    assert get_day_of_week(datetime(2026, 11, 22)) == "sunday"
    # 2026-11-23 is Monday
    assert get_day_of_week(datetime(2026, 11, 23)) == "monday"
    # 2026-11-26 is Thursday
    assert get_day_of_week(datetime(2026, 11, 26)) == "thursday"
    # 2026-11-27 is Friday
    assert get_day_of_week(datetime(2026, 11, 27)) == "friday"
    # 2026-11-28 is Saturday
    assert get_day_of_week(datetime(2026, 11, 28)) == "saturday"

def test_is_arrival_on_time():
    event_start = datetime(2026, 10, 5, 18, 0, 0)
    
    # Arrived 10 minutes early -> on time
    early = datetime(2026, 10, 5, 17, 50, 0)
    assert is_arrival_on_time(early, event_start) is True

    # Arrived exactly at start -> on time
    exact = datetime(2026, 10, 5, 18, 0, 0)
    assert is_arrival_on_time(exact, event_start) is True

    # Arrived 12 minutes after start (within 15m grace) -> on time
    within_grace = datetime(2026, 10, 5, 18, 12, 0)
    assert is_arrival_on_time(within_grace, event_start) is True

    # Arrived 20 minutes after start -> late
    late = datetime(2026, 10, 5, 18, 20, 0)
    assert is_arrival_on_time(late, event_start) is False
