# 📋 Slice 3: Profile Counters Engine (Dual Ingestion: Webhook + Batch Sync)

> **Goal:** Build a robust, decoupled Profile Counters Engine in `entry-recommendation-service` that supports **both ingestion models**:
> 1. **Real-time Webhook/Endpoint:** For instant updates triggered on check-in events (`POST /api/profiles/events/entry`).
> 2. **Batch / Backfill Sync:** For periodic synchronization and historical calculation across all entries without requiring immediate webhooks.

---

## 🎯 1. Frame (Requirements & Boundaries)

1. **Dual Ingestion Paths:**
   - **Path A: Real-Time Ingestion (Hook Endpoint):**
     - Endpoint: `POST /api/profiles/events/entry`
     - Payload: `{ "participant_id": str, "event_id": str, "entry_time": Optional[datetime] }`
     - Fast execution: Resolves event category, time bucket, and day of week, then applies atomic MongoDB update (`$inc`).
     - Returns HTTP 200/202 (fire-and-forget compatible from the main Node.js backend).
   - **Path B: Batch Sync & Backfill:**
     - Endpoint: `POST /api/profiles/sync/batch` (or CLI script `run_batch_sync.py`).
     - Parameters: `full_rebuild: bool = False`, `since: Optional[datetime] = None`.
     - High throughput: Groups entries by participant and applies updates via MongoDB `bulk_write` in chunks (e.g. 500 participants per batch).

2. **Atomic Profile Mutation (`$inc`):**
   - The engine is the single point of logic mutating `stats` on MongoDB `participants`:
     - `stats.categories.<category_id> += 1`
     - `stats.time_buckets.<bucket_id> += 1`
     - `stats.days_of_week.<day_id> += 1` (e.g. `sunday`, `monday`, etc.)
     - `stats.total_attendances += 1`
     - `stats.last_active = max(existing, entry_time)`
   - Safe against missing fields: Automatically initializes the `stats` subdocument without corrupting participant data.

3. **No Direct Dependency on External Services:**
   - Works directly against MongoDB collections (`participants`, `events`, `entries`).
   - If the main Node.js backend does not call the webhook, the system can run entirely on periodic batch sync.

---

## 🛠️ 2. Plan (File Structure & Architecture)

```text
entry-recommendation-service/
├── app/
│   ├── profiles/
│   │   ├── __init__.py
│   │   ├── schemas.py           # EntryHookPayload, BatchSyncRequest, BatchSyncResponse
│   │   ├── engine.py            # ProfileEngine (atomic single-record $inc updates)
│   │   └── batch.py             # BatchSyncService (chunked historical & periodic sync via bulk_write)
│   ├── routers/
│   │   └── profiles.py          # FastAPI routes: POST /events/entry (hook) & POST /sync/batch
│   └── scripts/
│       └── run_batch_sync.py    # Command-line utility to run batch sync on demand
└── tests/
    └── test_slice3_profile_counters.py # Tests for hook endpoint, atomic $inc, and batch sync
```

---

## 📝 3. Detailed Component Specifications

### A. Schemas (`schemas.py`)
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class EntryHookPayload(BaseModel):
    participant_id: str
    event_id: str
    entry_time: Optional[datetime] = Field(default_factory=datetime.utcnow)

class BatchSyncRequest(BaseModel):
    full_rebuild: bool = False
    batch_size: int = 500
    since: Optional[datetime] = None

class BatchSyncResponse(BaseModel):
    total_entries_processed: int
    participants_updated: int
    duration_seconds: float
```

### B. Core Profile Engine (`engine.py`)
```python
from bson import ObjectId
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

class ProfileEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.participants = db["participants"]
        self.events = db["events"]

    async def record_entry_atomic(
        self,
        participant_id: str,
        category_id: str,
        time_bucket: str,
        day_of_week: str,
        entry_time: datetime
    ) -> bool:
        obj_id = ObjectId(participant_id) if isinstance(participant_id, str) else participant_id

        update_query = {
            "$inc": {
                f"stats.categories.{category_id}": 1,
                f"stats.time_buckets.{time_bucket}": 1,
                f"stats.days_of_week.{day_of_week}": 1,
                "stats.total_attendances": 1,
            },
            "$set": {
                "stats.last_active": entry_time
            }
        }

        result = await self.participants.update_one({"_id": obj_id}, update_query)
        return result.modified_count > 0
```

### C. Webhook Router (`routers/profiles.py`)
```python
@router.post("/events/entry", status_code=status.HTTP_200_OK)
async def handle_entry_hook(
    payload: EntryHookPayload,
    engine: ProfileEngine = Depends(get_profile_engine),
    classifier: BaseEventClassifier = Depends(get_classifier)
):
    """
    Hook called whenever an entry is scanned.
    Resolves category, time bucket, day of week, and updates participant counters in MongoDB.
    """
    event = await engine.get_event(payload.event_id)
    entry_dt = payload.entry_time or event.get("date") or datetime.utcnow()
    
    classification = await classifier.classify(event["name"], event.get("description"))
    time_bucket = get_time_bucket(entry_dt)
    day_of_week = get_day_of_week(entry_dt)

    await engine.record_entry_atomic(
        participant_id=payload.participant_id,
        category_id=classification.category_id,
        time_bucket=time_bucket,
        day_of_week=day_of_week,
        entry_time=entry_dt
    )
    return {
        "status": "success",
        "category": classification.category_id,
        "bucket": time_bucket,
        "day": day_of_week
    }
```

---

## 🔍 4. Verification & Definition of Done

* [ ] **Hook Endpoint Verification:** `POST /api/profiles/events/entry` increments `stats.categories`, `stats.time_buckets`, `stats.days_of_week`, and `stats.total_attendances` correctly.
* [ ] **Batch Sync Accuracy:** Running batch sync properly extracts day of week from historical timestamps and populates `stats.days_of_week`.
* [ ] **Bulk Write Performance:** Batch mode processes entries in chunked `BulkWrite`, minimizing database roundtrips.
* [ ] **Test Coverage:** All automated tests in `tests/test_slice3_profile_counters.py` pass with exit code 0.
