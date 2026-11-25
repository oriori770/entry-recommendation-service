# 📋 Slice 6: FastAPI Endpoints, JWT Security & End-to-End Orchestration

> **Target:** Wire all components (Classification, Profiling, Retrieval, and AI Scoring) into production-ready FastAPI endpoints with shared JWT authentication, CORS, lifespan database management, and end-to-end integration tests.

---

## 🎯 1. Frame (Requirements & Boundaries)

### 1.1 API Endpoints
1. `GET /health` - Health check verifying MongoDB connectivity.
2. `POST /api/recommendations/events/{event_id}`:
   * Query params: `top_k: int = 10`, `group_type: Optional[str] = None`.
   * Workflow:
     1. Fetch `Event` from MongoDB by ID.
     2. Classify event dynamically if category is missing (Slice 2).
     3. Retrieve factual candidates from MongoDB matching event attributes (Slice 4).
     4. Grounded AI Scorer normalizes scores (0-100) and writes Hebrew reasoning (Slice 5).
     5. Returns `List[ParticipantRecommendation]`.
3. `POST /api/profiles/backfill`:
   * Trigger retroactive historical counters calculation across all participant entries (Slice 3).
4. `GET /api/tenants/{group_id}/categories`:
   * Return dynamic active categories configured for the organization.

### 1.2 Authentication & Security
* JWT verification middleware/dependency matching the Node.js backend (`JWT_SECRET`).
* Extract and validate Bearer Token on protected endpoints.

---

## 🛠️ 2. File Structure

```text
entry-recommendation-service/
├── app/
│   ├── auth.py                          # JWT Bearer validation dependency
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py                    # GET /health
│   │   ├── recommendations.py           # POST /api/recommendations/...
│   │   └── tenants.py                   # GET /api/tenants/...
│   ├── main.py                          # FastAPI app entry point & lifespan
│   └── recommendations/
│       └── service.py                   # RecommendationService orchestrator
├── tests/
│   └── test_recommendation_flow.py      # Full E2E API integration tests
└── plans/
    └── slice-6-recommendation-api.md
```

---

## 🔍 3. Verification & Done Criteria

- [ ] All routes registered and functional under FastAPI.
- [ ] Protected routes reject unauthenticated requests (HTTP 401).
- [ ] End-to-end recommendation flow runs cleanly from event ID to ranked, reasoned response.
- [ ] 100% of test suite passing in pytest.
