import pytest
from datetime import datetime
from app.classification.time_buckets import get_time_bucket
from app.models.stats import TimeBucketEnum

@pytest.mark.parametrize("hour,minute,expected", [
    (6, 0, TimeBucketEnum.MORNING.value),
    (8, 30, TimeBucketEnum.MORNING.value),
    (11, 59, TimeBucketEnum.MORNING.value),
    (12, 0, TimeBucketEnum.AFTERNOON.value),
    (14, 15, TimeBucketEnum.AFTERNOON.value),
    (16, 59, TimeBucketEnum.AFTERNOON.value),
    (17, 0, TimeBucketEnum.EVENING.value),
    (19, 45, TimeBucketEnum.EVENING.value),
    (20, 59, TimeBucketEnum.EVENING.value),
    (21, 0, TimeBucketEnum.NIGHT.value),
    (23, 59, TimeBucketEnum.NIGHT.value),
    (0, 0, TimeBucketEnum.NIGHT.value),
    (3, 30, TimeBucketEnum.NIGHT.value),
    (5, 59, TimeBucketEnum.NIGHT.value),
])
def test_get_time_bucket_boundaries(hour, minute, expected):
    dt = datetime(2026, 10, 15, hour, minute, 0)
    assert get_time_bucket(dt) == expected
