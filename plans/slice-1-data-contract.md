# 📋 Slice 1: Data Contracts, Core Schemas & Temporal Extraction

> **Goal:** Establish Pydantic v2 data models for participants, events, entries, and behavioral counter stats—fully aligned with the existing MongoDB models (`tishrei-entry-backend`)—along with deterministic time-bucket and day-of-week extraction utilities and an asynchronous MongoDB connection layer.

---

## 🎯 1. Frame (Requirements & Boundaries)

1. **System Schema Alignment (`tishrei-entry-backend`):**
   - **`Participant`**:
     - Core fields: `name`, `family`, `barcode`, `phone`, `email` (optional), `city` (optional), `schoolClass` (optional), `branch` (optional), `groupType` (`GroupType` enum string), `isApproved` (bool), `createdAt`, `updatedAt`.
     - Behavioral extensions (`stats` subdocument, optional/default-safe).
   - **`ParticipantStats` (Multi-Dimensional Counters):**
     - `categories`: `Dict[str, int]` (counts per category ID, e.g. `sports`, `torah_study`).
     - `time_buckets`: `Dict[str, int]` (counts per time slot, e.g. `morning_06_12`, `evening_17_21`).
     - `days_of_week`: `Dict[str, int]` (counts per day name, e.g. `sunday`, `monday`, ..., `saturday`).
     - `total_attendances`: `int` (total visits across all events).
     - `last_active`: `Optional[datetime]` (most recent check-in timestamp).
   - **`Event`**:
     - `name`, `date`, `description` (optional), `isActive` (bool), `createdAt`, `updatedAt`.
   - **`Entry`**:
     - `participantId`, `eventId`, `scannerId`, `entryTime`, `method` (`barcode` | `manual`).

2. **Deterministic Temporal Extraction Utilities:**
   - `get_time_bucket(dt: datetime) -> str`:
     - `morning_06_12` (06:00 - 11:59)
     - `afternoon_12_17` (12:00 - 16:59)
     - `evening_17_21` (17:00 - 20:59)
     - `night_21_06` (21:00 - 05:59)
   - `get_day_of_week(dt: datetime) -> str`:
     - Standardized English lowercase day: `sunday`, `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`.

3. **Asynchronous MongoDB Access:**
   - Motor (`AsyncIOMotorClient`) connection lifecycle with safe startup/shutdown events.

---

## 🛠️ 2. Plan (File Structure)

```text
entry-recommendation-service/
├── app/
│   ├── config.py                 # Settings (MONGODB_URI, DB_NAME, PORT)
│   ├── database.py               # Motor async client & lifespan management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py               # PyObjectId (safe ObjectId serialization in Pydantic v2)
│   │   ├── stats.py              # ParticipantStats, TimeBucketEnum, DayOfWeekEnum
│   │   ├── participant.py        # ParticipantRead, ParticipantInDB, GroupTypeEnum
│   │   ├── event.py              # EventRead, EventInDB
│   │   └── entry.py              # EntryRead, EntryInDB
│   └── classification/
│       ├── __init__.py
│       └── temporal.py           # get_time_bucket & get_day_of_week helpers
└── tests/
    ├── conftest.py               # Fixtures with realistic backend data mocks
    └── test_slice1_contracts.py  # Unit tests for schemas & temporal calculation
```

---

## 📝 3. Component Code Specifications

### A. Temporal Calculations (`temporal.py`)
```python
from datetime import datetime

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

def get_day_of_week(dt: datetime) -> str:
    """Returns normalized lowercase day name: sunday..saturday."""
    return DAYS[dt.weekday()]

def get_time_bucket(dt: datetime) -> str:
    """Maps a datetime to one of four deterministic daily slots."""
    hour = dt.hour
    if 6 <= hour < 12:
        return "morning_06_12"
    elif 12 <= hour < 17:
        return "afternoon_12_17"
    elif 17 <= hour < 21:
        return "evening_17_21"
    else:
        return "night_21_06"
```

### B. Participant & Stats Schemas (`stats.py` & `participant.py`)
```python
from enum import Enum
from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.base import PyObjectId

class GroupType(str, Enum):
    HIGH_SCHOOL_FULL_MONTH = "תיכון תוכניות חודש מלא"
    HIGH_SCHOOL_PARTIAL = "חודש חלקי (אחרי יו\"כ)"
    APARTMENT_PLUS_PROGRAMS = "דירה + תוכניות"
    SEMINAR_FULL_MONTH = "סמינר - תוכניות חודש מלא"
    SEMINAR_AFTER_YOM = "סמינר - תוכניות אחרי יו\"כ"
    WOMEN = "נשים"

class ParticipantStats(BaseModel):
    categories: Dict[str, int] = Field(default_factory=dict)
    time_buckets: Dict[str, int] = Field(default_factory=dict)
    days_of_week: Dict[str, int] = Field(default_factory=dict)
    total_attendances: int = 0
    last_active: Optional[datetime] = None

class ParticipantRead(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    family: str
    barcode: str
    phone: str
    email: Optional[str] = None
    city: Optional[str] = None
    school_class: Optional[str] = Field(default=None, alias="schoolClass")
    branch: Optional[str] = None
    group_type: str = Field(alias="groupType")
    is_approved: bool = Field(default=False, alias="isApproved")
    stats: ParticipantStats = Field(default_factory=ParticipantStats)
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

    class Config:
        populate_by_name = True
```

---

## 🔍 4. Verification & Definition of Done

* [ ] **Backend Schema Fidelity:** Pydantic models can parse real participant JSON documents from `tishrei-entry-backend` without validation errors.
* [ ] **Temporal Accuracy:** `get_time_bucket` and `get_day_of_week` produce 100% deterministic, accurate mappings across all 24 hours, edge bounds, and weekday transitions.
* [ ] **Default Robustness:** Documents lacking the `stats` field automatically instantiate clean, empty default dictionaries.
* [ ] **Pytest Verification:** `pytest tests/test_slice1_contracts.py` passes with 0 failures.
