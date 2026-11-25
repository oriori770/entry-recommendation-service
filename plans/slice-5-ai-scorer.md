# 📋 Slice 5: Grounded AI Scorer & Factual Reasoner

> **Target:** Implement the AI Scorer layer that evaluates candidate matches retrieved from MongoDB, normalizes a final score (0-100), and generates persuasive, factual Hebrew reasoning based strictly on behavioral counters without hallucinations.

---

## 🎯 1. Frame (Requirements & Boundaries)

### 1.1 Output Contract (`ParticipantRecommendation`)
```python
class ParticipantRecommendation(BaseModel):
    participant_id: str
    participant_name: str
    phone: Optional[str] = None
    city: Optional[str] = None
    group_type: Optional[str] = None
    score: int  # Normalized 0-100
    reasoning: str  # Factual Hebrew explanation
    breakdown: Dict[str, Any]  # Metrics behind the recommendation
```

### 1.2 Grounded Prompting Principles (PCTCO)
* **P**ersona: Community engagement & attendance coordinator.
* **C**ontext: Event name, category, day of week, time bucket.
* **T**ask: Generate concise Hebrew reasoning explaining why each participant is recommended.
* **C**onstraints: Strictly grounded in provided counters (category attendances, time of day regularity, streak, punctuality). No hallucinations.
* **O**utput: Structured JSON with list of reasoned recommendations.

### 1.3 Provider Agnostic Design
* `AIScorerPort` (Protocol)
* `MockAIScorer` (Deterministic template-based reasoner for zero-cost testing)
* `LLMAIScorer` (Supports Ollama local models, OpenAI, and Gemini)

---

## 🛠️ 2. File Structure

```text
entry-recommendation-service/
├── app/
│   └── recommendations/
│       ├── ai_scorer_port.py       # AIScorerPort protocol & models
│       ├── ai_prompts.py           # Grounded prompts
│       ├── ai_scorer_mock.py       # Deterministic template reasoner
│       └── ai_scorer_llm.py        # Generic LLM Scorer (Local/Cloud)
├── tests/
│   └── test_ai_scorer.py           # Verification of score normalization and reasoning
└── plans/
    └── slice-5-ai-scorer.md
```

---

## 🔍 3. Verification & Done Criteria

- [ ] Score normalization maps diverse raw candidate scores smoothly to 0-100.
- [ ] Hebrew reasoning directly quotes and references actual behavioral metrics (e.g. category count, streak).
- [ ] Mock and LLM implementations adhere to the unified `AIScorerPort`.
- [ ] Automated tests pass in pytest.
