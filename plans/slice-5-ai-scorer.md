# 📋 Slice 5: Grounded AI Scorer & Hebrew Reasoner (Chunked & Configurable Batching)

> **Goal:** Build the AI Scoring & Reasoning engine that evaluates pre-filtered candidates (from Slice 4) against event details using an LLM. Candidate batches are processed in **configurable chunk sizes** (supporting both small Top-K and large 1,000+ candidate workloads via parallel/sequential chunking) to prevent context window overflow and token timeouts, producing human-readable Hebrew justifications with strict grounding.

---

## 🎯 1. Frame (Requirements & Boundaries)

1. **Configurable Chunked Batching (`llm_batch_size`):**
   - Scoring large sets of candidates (e.g. $K=1000$ or $K=50$) must not be forced into a single massive LLM call.
   - Batch size per LLM invocation is configurable via settings or request:
     - Default: `llm_batch_size = 20` (optimal for latency, context window, and structured JSON output stability).
   - If Total Candidates $K > \text{batch\_size}$:
     - The candidate list is chunked into sub-batches: $[0..\text{batch\_size}], [\text{batch\_size}..2\cdot\text{batch\_size}], \dots$
     - Sub-batches can be executed sequentially or concurrently (with configurable concurrency limit `max_concurrent_llm_calls = 3` to respect provider rate limits).
     - Results are aggregated, validated, and merged back into the final ordered recommendation response.

2. **Zero-Hallucination Grounding (PCTCO Framework):**
   - The LLM must generate explanations **strictly derived from the injected candidate counters**:
     - Category attendance count (`category_count`).
     - Time slot activity (`time_bucket_count`).
     - Day of the week activity (`day_of_week_count`).
     - Total attendance & recency.
   - Prohibited from inventing facts not present in the input context.

3. **Hebrew Language Justification:**
   - Fluent, natural Hebrew reasoning grounded in real numbers.
   - Example: *"נכח ב-7 אירועי ספורט בעבר, פעיל באופן עקבי בימי חמישי בערב (9 כניסות), ובעל נוכחות כוללת גבוהה."*

4. **Normalized Score (0 - 100):**
   - Output normalized to an integer `fit_score` between `0` and `100`.

5. **Testability & Offline Mocking:**
   - `MockAIScorer` providing deterministic mock outputs for automated test suites (Pytest) across both small and chunked large datasets.

---

## 🛠️ 2. Plan (File Structure & Architecture)

```text
entry-recommendation-service/
├── app/
│   ├── recommendations/
│   │   ├── __init__.py
│   │   ├── schemas.py           # ScoredCandidate, BatchScoringConfig
│   │   ├── prompts.py           # PCTCO system & chunk prompt templates
│   │   ├── chunker.py           # Utilities for partitioning candidates & gathering results
│   │   ├── ai_scorer.py         # BaseAIScorer, LLMAIScorer, MockAIScorer
│   │   └── validator.py         # Grounding validator (detects unsupported claims)
└── tests/
    └── test_slice5_ai_scorer.py # Unit tests for chunking, concurrency, and grounding
```

---

## 📝 3. Detailed Component Specifications

### A. Schemas & Batch Config (`schemas.py`)
```python
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class BatchScoringConfig(BaseModel):
    batch_size: int = Field(default=20, ge=1, le=100, description="Max candidates per single LLM call")
    max_concurrency: int = Field(default=3, ge=1, le=10, description="Max parallel LLM calls")

class CandidateInput(BaseModel):
    id: str
    name: str
    city: Optional[str] = None
    group_type: Optional[str] = None
    category_count: int
    time_bucket_count: int
    day_of_week_count: int
    total_attendances: int
    computed_score: float

class ScoredCandidate(BaseModel):
    participant_id: str
    name: str
    city: Optional[str] = None
    group_type: Optional[str] = None
    fit_score: int = Field(ge=0, le=100, description="Normalized score 0-100")
    reasoning: str = Field(description="Clear Hebrew explanation grounded in numbers")
    highlight_metrics: Dict[str, int] = Field(default_factory=dict)
```

### B. Candidate Chunking & Execution Flow (`chunker.py`)
```python
import asyncio
from typing import List, Callable, Awaitable
from app.recommendations.schemas import CandidateInput, ScoredCandidate, BatchScoringConfig

def partition_candidates(candidates: List[CandidateInput], chunk_size: int) -> List[List[CandidateInput]]:
    """Splits candidate list into chunks of at most chunk_size."""
    return [candidates[i : i + chunk_size] for i in range(0, len(candidates), chunk_size)]

async def process_chunks_concurrently(
    chunks: List[List[CandidateInput]],
    scoring_func: Callable[[List[CandidateInput]], Awaitable[List[ScoredCandidate]]],
    max_concurrency: int = 3
) -> List[ScoredCandidate]:
    """
    Executes scoring functions over candidate chunks respecting a semaphore limit.
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def worker(chunk: List[CandidateInput]) -> List[ScoredCandidate]:
        async with semaphore:
            return await scoring_func(chunk)

    tasks = [worker(chunk) for chunk in chunks]
    results_nested = await asyncio.gather(*tasks)
    
    # Flatten results
    flat_results = [item for sublist in results_nested for item in sublist]
    # Maintain descending order by fit_score
    return sorted(flat_results, key=lambda x: x.fit_score, reverse=True)
```

### C. AI Scorer Interface (`ai_scorer.py`)
```python
class BaseAIScorer(ABC):
    @abstractmethod
    async def score_and_reason(
        self,
        event_name: str,
        category_label: str,
        time_bucket: str,
        day_of_week: str,
        candidates: List[CandidateInput],
        config: Optional[BatchScoringConfig] = None
    ) -> List[ScoredCandidate]:
        pass
```

---

## 🔍 4. Verification & Definition of Done

* [ ] **Chunking Behavior:** If $K=65$ candidates and `batch_size=20`, exactly 4 LLM calls are dispatched (three of 20, one of 5).
* [ ] **Concurrency Control:** Semaphore limits concurrent calls to `max_concurrency`, avoiding rate limit / 429 errors from LLM providers.
* [ ] **Grounding Verification:** The generated Hebrew reasoning strictly uses numerical stats present in the candidate profile (no hallucinations).
* [ ] **Safe Bounds:** All `fit_score` values are validated within the `0..100` range.
* [ ] **Mock Test Coverage:** `tests/test_slice5_ai_scorer.py` tests both single-chunk and multi-chunk partitioning offline with 100% pass rate.
