# 📋 Slice 6: Recommendation Orchestration API, Security & E2E Verification

> **Goal:** Build the complete end-to-end recommendation flow and public API endpoints (`POST /api/recommendations/events/{event_id}`), secure the service with JWT authentication matching the existing backend, and implement Rule-as-a-Test end-to-end test suites.

---

## 🎯 1. Frame (Requirements & Boundaries)

1. **End-to-End Recommendation Pipeline Orchestration:**
   - Single entrypoint orchestrating all previous slices:
     1. **Fetch Event:** Retrieve target event from MongoDB (`EventModel`).
     2. **Classify & Temporal:** Extract category (Slice 2) and determine time bucket + day of week (Slice 1).
     3. **Candidate Retrieval:** Query MongoDB with hard exclusions (`already checked-in`) and group constraints to retrieve Top-K deterministically scored candidates (Slice 4).
     4. **AI Scoring & Hebrew Reasoning:** Partition candidates into configurable chunks (`BatchScoringConfig`) and generate grounded Hebrew reasoning (Slice 5).
     5. **Response Delivery:** Return structured recommendations with metadata and execution metrics.

2. **Public API Endpoints:**
   - `POST /api/recommendations/events/{event_id}`:
     - Query / Body params: `limit` (default: 20), `allowed_group_types`, `batch_size`, `min_score`.
   - `POST /api/recommendations/custom`:
     - Allows ad-hoc recommendation for an event not yet in the DB (accepts custom `name`, `date`, `description`).
   - `GET /api/recommendations/health`:
     - Service health, MongoDB connectivity status, and taxonomy version info.

3. **Security & Authorization (JWT Middleware):**
   - Decode and verify JWT tokens signed with the existing `JWT_SECRET` from `tishrei-entry-backend`.
   - Role-Based Access Control (RBAC):
     - Gated to `admin` and `superadmin` roles only. Scanners (`scanner`) or unauthenticated users receive HTTP 401/403.

4. **Rule-as-a-Test & E2E Testing:**
   - Full flow testing from HTTP request to response.
   - Grounding validation: Asserts that no candidate contains an empty explanation or hallucinated metric.
   - Security tests: Asserts that requests lacking valid JWT or valid role are rejected.

---

## 🛠️ 2. Plan (File Structure & Architecture)

```text
entry-recommendation-service/
├── app/
│   ├── auth.py                  # JWT validation & user role dependency (admin/superadmin)
│   ├── recommendations/
│   │   ├── service.py           # RecommendationOrchestrator (coordinates slices 1-5)
│   │   └── schemas.py           # Final API Request & Response models
│   └── routers/
│       ├── health.py            # Health and diagnostic endpoints
│       └── recommendations.py   # Public Recommendation API router
└── tests/
    ├── test_auth.py             # JWT & RBAC tests (401/403 validation)
    ├── test_e2e_recommendations.py # End-to-end flow with Mock LLM
    └── test_rule_as_a_test.py   # Grounding & safety invariants verification
```

---

## 📝 3. Detailed Component Specifications

### A. Recommendation Request & Response Schemas (`schemas.py`)
```python
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class RecommendationOptions(BaseModel):
    limit: int = Field(default=20, ge=1, le=1000)
    allowed_group_types: Optional[List[str]] = None
    city_filter: Optional[str] = None
    batch_size: int = Field(default=20, ge=1, le=100)
    max_concurrency: int = Field(default=3, ge=1, le=10)

class RecommendedCandidateItem(BaseModel):
    participant_id: str
    name: str
    phone: Optional[str] = None
    city: Optional[str] = None
    group_type: Optional[str] = None
    fit_score: int
    reasoning: str
    metrics: Dict[str, Any]

class RecommendationResponse(BaseModel):
    event_id: str
    event_name: str
    category_id: str
    time_bucket: str
    day_of_week: str
    total_candidates_found: int
    recommendations: List[RecommendedCandidateItem]
    execution_time_ms: float
```

### B. Service Orchestrator (`service.py`)
```python
import time
from app.classification.temporal import get_time_bucket, get_day_of_week

class RecommendationService:
    def __init__(self, db, classifier, retriever, ai_scorer):
        self.db = db
        self.classifier = classifier
        self.retriever = retriever
        self.ai_scorer = ai_scorer

    async def get_recommendations_for_event(
        self,
        event_id: str,
        options: RecommendationOptions
    ) -> RecommendationResponse:
        start_time = time.perf_counter()

        # 1. Fetch Event
        event = await self.db["events"].find_one({"_id": ObjectId(event_id)})
        if not event:
            raise NotFoundException(f"Event {event_id} not found")

        event_date = event.get("date", datetime.utcnow())

        # 2. Classify Event & Temporal Dimensions
        classification = await self.classifier.classify(event["name"], event.get("description"))
        time_bucket = get_time_bucket(event_date)
        day_of_week = get_day_of_week(event_date)

        # 3. Retrieve Candidates (with hard exclusions & constraints)
        candidates = await self.retriever.get_top_candidates(
            RetrievalParams(
                event_id=event_id,
                category_id=classification.category_id,
                time_bucket=time_bucket,
                day_of_week=day_of_week,
                limit=options.limit,
                allowed_group_types=options.allowed_group_types,
                city_filter=options.city_filter
            )
        )

        if not candidates:
            return RecommendationResponse(
                event_id=event_id,
                event_name=event["name"],
                category_id=classification.category_id,
                time_bucket=time_bucket,
                day_of_week=day_of_week,
                total_candidates_found=0,
                recommendations=[],
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

        # 4. Chunked AI Scoring & Hebrew Reasoning
        scoring_config = BatchScoringConfig(
            batch_size=options.batch_size,
            max_concurrency=options.max_concurrency
        )
        scored = await self.ai_scorer.score_and_reason(
            event_name=event["name"],
            category_label=classification.category_id,
            time_bucket=time_bucket,
            day_of_week=day_of_week,
            candidates=candidates,
            config=scoring_config
        )

        duration = (time.perf_counter() - start_time) * 1000
        return RecommendationResponse(
            event_id=event_id,
            event_name=event["name"],
            category_id=classification.category_id,
            time_bucket=time_bucket,
            day_of_week=day_of_week,
            total_candidates_found=len(scored),
            recommendations=scored,
            execution_time_ms=duration
        )
```

### C. FastAPI Router (`routers/recommendations.py`)
```python
@router.post("/events/{event_id}", response_model=RecommendationResponse)
async def recommend_for_event(
    event_id: str,
    options: RecommendationOptions = RecommendationOptions(),
    current_user: AuthenticatedUser = Depends(require_role(["admin", "superadmin"])),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Main recommendation endpoint. Gated to Admin/SuperAdmin.
    """
    return await service.get_recommendations_for_event(event_id, options)
```

---

## 🔍 4. Verification & Definition of Done

* [ ] **Full Flow E2E:** `POST /api/recommendations/events/{id}` returns accurate candidates with validated Hebrew reasoning and correct scores.
* [ ] **RBAC Security:** Unauthenticated calls return HTTP 401; scanner roles return HTTP 403; admin/superadmin succeed with HTTP 200.
* [ ] **Rule-as-a-Test Invariants:**
  - Invariant 1: No recommended candidate has already checked-in to the event.
  - Invariant 2: Candidate group types strictly conform to `allowed_group_types`.
  - Invariant 3: Explanations never contradict the factual profile numbers.
* [ ] **Test Coverage:** All test suites (`test_auth.py`, `test_e2e_recommendations.py`, `test_rule_as_a_test.py`) execute and pass cleanly with exit code 0.
