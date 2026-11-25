# 📋 Slice 4: Smart Candidate Retrieval & Scoring Engine

> **Target:** Build a MongoDB candidate retrieval engine that computes factual compatibility scores across behavioral counters (category, time slot, day of week, streak, punctuality) and returns top-K ranked candidates for any event without requiring LLM calls.

---

## 🎯 1. Frame (Requirements & Boundaries)

### 1.1 Configurable Scoring Weights (`ScoringWeights`)
* `weight_category: float = 40.0` - Affinity to event's category
* `weight_time_bucket: float = 25.0` - Activity during the event's diurnal time window
* `weight_day_of_week: float = 15.0` - Regularity on this specific day of the week
* `weight_streak: float = 10.0` - Bonus for active attendance streaks
* `weight_punctuality: float = 10.0` - Bonus for consistent punctuality

### 1.2 Output Contract (`CandidateMatch`)
```python
class CandidateMatch(BaseModel):
    participant_id: str
    participant_name: str
    phone: Optional[str] = None
    city: Optional[str] = None
    group_type: Optional[str] = None
    total_score: float
    breakdown: Dict[str, Any]  # Category visits, time slot visits, streak, etc.
```

### 1.3 Retrieval Engine (`MongoCandidateRetriever`)
* Queries participants matching organization/group filters.
* Computes deterministic composite match score against event attributes.
* Sorts by `total_score` descending and returns Top-K candidates.

---

## 🛠️ 2. File Structure

```text
entry-recommendation-service/
├── app/
│   └── recommendations/
│       ├── __init__.py
│       ├── scoring_config.py       # ScoringWeights & CandidateMatch
│       └── retrieval.py            # MongoCandidateRetriever
├── tests/
│   └── test_retrieval.py           # Ranking, weighting, and top-k retrieval tests
└── plans/
    └── slice-4-mongo-retrieval.md
```

---

## 🔍 3. Verification & Done Criteria

- [ ] Scoring accurately reflects participant affinity (a participant with high football counts scores highest for a football event).
- [ ] Top-K sorting and limit parameters function as expected.
- [ ] Score breakdown provides transparent, explainable metrics for downstream LLM reasoning.
- [ ] 100% passing tests in pytest.
