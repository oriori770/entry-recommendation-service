# 📋 Slice 1: Data Contracts, Behavioral Counter Models & Time Buckets

> **Target:** Establish robust Pydantic v2 data models for Participants, Events, Entries, and Behavioral Stats, implement a deterministic Time Bucketing mechanism for activity time distribution, set up async MongoDB connectivity, and verify with automated pytest suites.

---

## 🎯 1. Frame (Requirements & Boundaries)

### 1.1 Data Models (Pydantic v2)
* **`ParticipantStats`**:
  * `categories: Dict[str, int]` - Frequency counter for each event category (default empty).
  * `time_buckets: Dict[str, int]` - Frequency counter for each diurnal time slot (default empty).
  * `total_attendances: int` - Total event participations counter (default 0).
  * `last_active: Optional[datetime]` - Timestamp of most recent participation.
* **`Participant`**:
  * Fields matching MongoDB `participants` collection: `id` (as `PyObjectId`), `name`, `family`, `barcode`, `phone`, `city` (optional), `groupType`, `isApproved`.
  * Behavioral stats: `stats: ParticipantStats` (default initialized).
* **`Event`**:
  * Fields matching MongoDB `events` collection: `id`, `name`, `date`, `description` (optional), `isActive`.
  * Enriched classification: `category: Optional[str]`, `time_bucket: Optional[str]`.
* **`Entry`**:
  * Fields matching MongoDB `entries` collection: `id`, `participantId`, `eventId`, `scannerId`, `entryTime`, `method`.

### 1.2 Time Buckets Specification
Deterministic segmentation of the 24-hour day into 4 practical operational windows:
* `morning_06_12` (06:00 - 11:59)
* `afternoon_12_17` (12:00 - 16:59)
* `evening_17_21` (17:00 - 20:59)
* `night_21_06` (21:00 - 05:59)
* Function: `get_time_bucket(dt: datetime) -> str`

### 1.3 Database Connectivity
* Asynchronous MongoDB client setup using `motor.motor_asyncio.AsyncIOMotorClient`.
* Pydantic configuration support for MongoDB `ObjectId` conversion (`PyObjectId` via `BeforeValidator` / `Annotated`).

---

## 🛠️ 2. File Structure & Responsibilities

```text
entry-recommendation-service/
├── app/
│   ├── __init__.py
│   ├── config.py                 # App settings (MONGODB_URI, DB_NAME)
│   ├── database.py               # Async MongoDB client lifecycle
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py               # PyObjectId type definition for MongoDB
│   │   ├── stats.py              # ParticipantStats & TimeBucketEnum
│   │   ├── participant.py        # ParticipantRead & ParticipantInDB
│   │   ├── event.py              # EventRead & EventInDB
│   │   └── entry.py              # EntryRead & EntryInDB
│   └── classification/
│       ├── __init__.py
│       └── time_buckets.py       # get_time_bucket logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Shared test fixtures & dummy documents
│   ├── test_models.py            # Pydantic parsing & validation tests
│   └── test_time_buckets.py      # Unit tests covering all 24 hours & edge cases
├── requirements.txt              # pydantic, motor, pytest, etc.
└── .env.example
```

---

## 📐 3. Implementation Steps

1. **Environment & Dependencies:**
   * Create `requirements.txt` with `pydantic>=2.7.0`, `motor>=3.4.0`, `pytest>=8.0.0`, `pytest-asyncio`, `python-dotenv`.
2. **PyObjectId & Base Support (`app/models/base.py`):**
   * Implement BSON `ObjectId` serialization/deserialization for Pydantic v2.
3. **Behavioral Stats & Models (`app/models/`):**
   * Define `ParticipantStats`, `Participant`, `Event`, `Entry`.
4. **Time Bucketing Engine (`app/classification/time_buckets.py`):**
   * Implement `get_time_bucket(dt: datetime) -> str` with rigorous boundary conditions.
5. **Database Connector (`app/database.py`):**
   * Async MongoDB connection lifecycle helper.
6. **Automated Testing Suite (`tests/`):**
   * Full test coverage for model serialization, schema validation, and hour boundary conditions.

---

## 🔍 4. Verification & Done Criteria

- [ ] All models parse real sample JSON data from `tishrei-entry-backend` without errors.
- [ ] `get_time_bucket` handles all edge timestamps (00:00, 05:59, 06:00, 11:59, 12:00, 16:59, 17:00, 20:59, 21:00, 23:59).
- [ ] Pydantic serialization roundtrip maintains `ObjectId` consistency.
- [ ] `pytest tests/` runs and passes with 100% green exit code.
