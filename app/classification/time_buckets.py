from datetime import datetime
from app.models.stats import TimeBucketEnum

def get_time_bucket(dt: datetime) -> str:
    """
    Classifies a datetime timestamp into one of 4 standardized diurnal time buckets.
    - morning_06_12:   [06:00, 12:00)
    - afternoon_12_17: [12:00, 17:00)
    - evening_17_21:   [17:00, 21:00)
    - night_21_06:     [21:00, 06:00)
    """
    hour = dt.hour
    if 6 <= hour < 12:
        return TimeBucketEnum.MORNING.value
    elif 12 <= hour < 17:
        return TimeBucketEnum.AFTERNOON.value
    elif 17 <= hour < 21:
        return TimeBucketEnum.EVENING.value
    else:
        return TimeBucketEnum.NIGHT.value
