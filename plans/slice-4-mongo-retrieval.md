# 📋 Slice 4: Candidate Retrieval & Deterministic Scoring Engine

> **Goal:** Build the Candidate Retrieval engine that queries MongoDB to find and rank the most relevant participants for a given event, using multi-dimensional behavioral counters (category + time bucket + day of the week + recency bonus) with hard constraints (group type filtering, deduplicating participants already checked-in) without relying on vector databases.

---

## 🎯 1. Frame (Requirements & Boundaries)

1. **Hard Filtering & Exclusion Constraints:**
   - **Exclusion of Already Checked-in Participants:** Query the `entries` collection for `eventId == target_event_id` and explicitly exclude these `participantId`s from recommendations (no point recommending someone who has already scanned into the event).
   - **Target Group Filtering (`groupType`):** If an event is designated for specific groups (e.g. `תיכון תוכניות חודש מלא` or `נשים`), filter participants whose `groupType` matches the allowed criteria.
   - **Approval Check:** Strictly enforce `isApproved: true`.

2. **Multi-Dimensional Grounded Scoring Formula:**
   - Candidate ranking is 100% deterministic and explainable:
     $$\text{Score} = (W_{\text{cat}} \cdot C_{\text{cat}}) + (W_{\text{time}} \cdot C_{\text{time}}) + (W_{\text{day}} \cdot C_{\text{day}}) + \text{Bonus}_{\text{recency}}$$
     Where:
     - $C_{\text{cat}}$: Attendance in the matching category (`stats.categories.<category_id>`).
     - $C_{\text{time}}$: Attendance in the matching time bucket (`stats.time_buckets.<bucket_id>`).
     - $C_{\text{day}}$: Attendance on the matching day of the week (`stats.days_of_week.<day_id>`).
     - $W_{\text{cat}}, W_{\text{time}}, W_{\text{day}}$: Configurable weights (default: $W_{\text{cat}} = 1.0$, $W_{\text{time}} = 0.5$, $W_{\text{day}} = 0.4$).
     - $\text{Bonus}_{\text{recency}}$: Small boost if `last_active` is within recent weeks.

3. **High-Performance MongoDB Aggregation Pipeline:**
   - Aggregation with safe field lookups (`$ifNull`), projection of calculated score, sorting, and Top-K limit.

4. **Structured Output for Downstream AI Scorer:**
   - Returns a structured list of candidates (`List[CandidateParticipant]`):
     - `participant_id`, `name`, `phone`, `city`, `branch`, `school_class`, `group_type`
     - `category_count`, `time_bucket_count`, `day_of_week_count`, `total_attendances`, `last_active`
     - `computed_score`

---

## 🛠️ 2. Plan (File Structure & Architecture)

```text
entry-recommendation-service/
├── app/
│   ├── recommendations/
│   │   ├── __init__.py
│   │   ├── schemas.py           # RetrievalParams, CandidateParticipant, RetrievalResult
│   │   ├── retrieval.py         # MongoCandidateRetriever (MongoDB aggregation pipeline & exclusions)
│   │   └── scoring_config.py    # Weights, thresholds, and recency decay configurations
└── tests/
    └── test_slice4_retrieval.py # Aggregation pipeline tests with mock MongoDB data
```

---

## 📝 3. Detailed Component Specifications

### A. Schemas (`schemas.py`)
```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class RetrievalParams(BaseModel):
    event_id: str
    category_id: str
    time_bucket: str
    day_of_week: str
    limit: int = Field(default=20, ge=1, le=100)
    allowed_group_types: Optional[List[str]] = None
    city_filter: Optional[str] = None
    weight_category: float = Field(default=1.0)
    weight_time_bucket: float = Field(default=0.5)
    weight_day_of_week: float = Field(default=0.4)
    recency_bonus_days: int = Field(default=30)
    recency_bonus_value: float = Field(default=2.0)

class CandidateParticipant(BaseModel):
    id: str
    name: str
    phone: Optional[str] = None
    city: Optional[str] = None
    branch: Optional[str] = None
    school_class: Optional[str] = None
    group_type: Optional[str] = None
    category_count: int = 0
    time_bucket_count: int = 0
    day_of_week_count: int = 0
    total_attendances: int = 0
    last_active: Optional[datetime] = None
    computed_score: float
```

### B. MongoDB Aggregation Pipeline with Exclusions (`retrieval.py`)
```python
from typing import List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.recommendations.schemas import RetrievalParams, CandidateParticipant

class MongoCandidateRetriever:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.participants = db["participants"]
        self.entries = db["entries"]

    async def get_excluded_participant_ids(self, event_id: str) -> List[ObjectId]:
        """Fetches participant IDs who already have an entry for this event."""
        target_event_oid = ObjectId(event_id) if isinstance(event_id, str) else event_id
        cursor = self.entries.find({"eventId": target_event_oid}, {"participantId": 1})
        existing_entries = await cursor.to_list(length=10000)
        return [doc["participantId"] for doc in existing_entries]

    async def get_top_candidates(self, params: RetrievalParams) -> List[CandidateParticipant]:
        # 1. Gather exclusions (already attended)
        excluded_ids = await self.get_excluded_participant_ids(params.event_id)

        # 2. Build match conditions
        match_query = {
            "isApproved": True,
            "_id": {"$nin": excluded_ids}
        }
        if params.allowed_group_types:
            match_query["groupType"] = {"$in": params.allowed_group_types}
        if params.city_filter:
            match_query["city"] = params.city_filter

        pipeline = [
            {"$match": match_query},
            
            # Safe field extraction
            {"$addFields": {
                "cat_count": {"$ifNull": [f"$stats.categories.{params.category_id}", 0]},
                "bucket_count": {"$ifNull": [f"$stats.time_buckets.{params.time_bucket}", 0]},
                "day_count": {"$ifNull": [f"$stats.days_of_week.{params.day_of_week}", 0]},
                "total_att": {"$ifNull": ["$stats.total_attendances", 0]},
                "last_act": "$stats.last_active"
            }},

            # Filter candidates with some relevant history
            {"$match": {
                "$or": [
                    {"cat_count": {"$gt": 0}},
                    {"bucket_count": {"$gt": 0}},
                    {"day_count": {"$gt": 0}},
                    {"total_att": {"$gt": 0}}
                ]
            }},

            # Multi-dimensional weighted score
            {"$addFields": {
                "computed_score": {
                    "$add": [
                        {"$multiply": ["$cat_count", params.weight_category]},
                        {"$multiply": ["$bucket_count", params.weight_time_bucket]},
                        {"$multiply": ["$day_count", params.weight_day_of_week]}
                    ]
                }
            }},

            {"$sort": {"computed_score": -1, "total_att": -1}},
            {"$limit": params.limit}
        ]

        cursor = self.participants.aggregate(pipeline)
        raw_results = await cursor.to_list(length=params.limit)
        
        return [
            CandidateParticipant(
                id=str(doc["_id"]),
                name=f"{doc.get('name', '')} {doc.get('family', '')}".strip(),
                phone=doc.get("phone"),
                city=doc.get("city"),
                branch=doc.get("branch"),
                school_class=doc.get("schoolClass"),
                group_type=doc.get("groupType"),
                category_count=doc.get("cat_count", 0),
                time_bucket_count=doc.get("bucket_count", 0),
                day_of_week_count=doc.get("day_count", 0),
                total_attendances=doc.get("total_att", 0),
                last_active=doc.get("last_act"),
                computed_score=float(doc.get("computed_score", 0.0))
            )
            for doc in raw_results
        ]
```

---

## 🔍 4. Verification & Definition of Done

* [ ] **Already Checked-in Exclusion:** A participant who already has an entry in `entries` for this event is strictly omitted from the returned candidates list.
* [ ] **Group Type Filtering:** When `allowed_group_types` is passed, candidates belonging to other groups are never returned.
* [ ] **Temporal & Category Accuracy:** Ranking reflects combined activity in category, time slot, and day of the week.
* [ ] **Test Coverage:** All unit/integration tests in `tests/test_slice4_retrieval.py` pass cleanly with exit code 0.
