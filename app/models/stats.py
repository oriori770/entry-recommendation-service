from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional
from datetime import datetime
from enum import Enum

class TimeBucketEnum(str, Enum):
    MORNING = "morning_06_12"
    AFTERNOON = "afternoon_12_17"
    EVENING = "evening_17_21"
    NIGHT = "night_21_06"

class DayOfWeekEnum(str, Enum):
    SUNDAY = "sunday"
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"

class PunctualityStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    on_time: int = Field(default=0, description="Arrivals within acceptable threshold (<= 15m after event start)")
    late: int = Field(default=0, description="Late arrivals (> 15m after event start)")

class StreakStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    current_streak: int = Field(default=0, description="Current consecutive event attendance count")
    longest_streak: int = Field(default=0, description="Longest consecutive attendance streak achieved")

class ParticipantStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    categories: Dict[str, int] = Field(default_factory=dict, description="Frequency per event category")
    time_buckets: Dict[str, int] = Field(default_factory=dict, description="Frequency per diurnal time bucket")
    days_of_week: Dict[str, int] = Field(default_factory=dict, description="Frequency per day of week (sunday..saturday)")
    punctuality: PunctualityStats = Field(default_factory=PunctualityStats, description="On-time vs late arrivals")
    streak: StreakStats = Field(default_factory=StreakStats, description="Attendance streak counters")
    total_attendances: int = Field(default=0, description="Total verified event visits")
    last_active: Optional[datetime] = Field(default=None, description="Timestamp of the most recent activity")
