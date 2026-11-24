# 📋 Slice 3: Profile Counters Engine & Historical Backfill

> **Target:** Implement the `ProfileEngine` for atomic, race-condition-free MongoDB profile counter updates (`$inc`), calculate streak increments, and implement a `BackfillService` capable of replaying historical entries across events to populate rich participant behavioral stats.

---

## 🎯 1. Frame (Requirements & Boundaries)

### 1.1 Atomic Counter Increment Logic
When a participant attends an event (`Entry`), update the participant document in MongoDB atomically:
```json
{
  "$inc": {
    "stats.categories.<category_key>": 1,
    "stats.time_buckets.<time_bucket>": 1,
    "stats.days_of_week.<day_name>": 1,
    "stats.punctuality.on_time": 1, // or stats.punctuality.late
    "stats.total_attendances": 1
  },
  "$set": {
    "stats.last_active": "<entry_time>"
  }
}
```

### 1.2 Streak Calculation Logic
* Compare `entry_time` with `stats.last_active`:
  * If within a streak window (e.g. `<= 7 days` or consecutive sequence): `current_streak += 1`.
  * If gap is too large: reset `current_streak = 1`.
  * If `current_streak > longest_streak`: update `longest_streak = current_streak`.

### 1.3 Backfill / Historical Replay Service
* Reads all historical entries grouped by participant.
* Enriches events with categories (utilizing cached categories from Slice 2).
* Calculates cumulative stats and updates participants in bulk or sequence.

---

## 🛠️ 2. File Structure

```text
entry-recommendation-service/
├── app/
│   └── profiles/
│       ├── __init__.py
│       ├── engine.py           # ProfileEngine: update_participant_profile & atomic updates
│       └── backfill.py         # BackfillService: historical replay
├── tests/
│   └── test_profile_engine.py  # Unit & Mock DB tests for atomic counter updates & backfill
└── plans/
    └── slice-3-profile-counters.md
```

---

## 🔍 3. Verification & Done Criteria

- [ ] Atomic update generation correctly constructs `$inc` and `$set` operators for all metrics (categories, time buckets, days of week, punctuality, streak).
- [ ] Streak calculation correctly handles continuations, resets on long inactivity, and updates longest streak records.
- [ ] Backfill service processes a batch of entries across multiple events and produces accurate aggregated participant stats.
- [ ] All unit tests pass in pytest.
