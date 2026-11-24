# 📋 Slice 2: Dynamic Multi-Tenant Event Classifier & Category Engine

> **Target:** Build a dynamic, multi-tenant event classification engine powered by LLM (with Port & Adapter architecture, supporting both Google Gemini and a fast deterministic Mock adapter for zero-cost testing), where categories and organization configurations are stored dynamically in MongoDB and can be managed per group/tenant.

---

## 🎯 1. Frame (Requirements & Boundaries)

### 1.1 Dynamic Tenant Schema
* **`CategoryDefinition`**:
  * `key: str` - System key stored in statistics (e.g. `football`, `farbrengen`).
  * `display_name: str` - User-facing label for frontend UI (e.g. `טורניר כדורגל`).
  * `description: str` - Guidelines describing this category for the LLM classifier.
  * `icon: Optional[str]` - UI icon identifier.
  * `is_active: bool` - Enables/disables category without removing history.
* **`TenantConfig`**:
  * `group_id: str` - Organization identifier (e.g. `temimim`, `anash`).
  * `display_name: str` - Tenant display name.
  * `categories: List[CategoryDefinition]` - Dynamic categories defined for this tenant.
  * `settings: Dict[str, Any]` - Custom configurations.

### 1.2 Output Contract
```python
class EventClassificationResult(BaseModel):
    category_key: str
    display_name: Optional[str]
    confidence: float  # 0.0 to 1.0
    reasoning: str
```

### 1.3 Port & Adapter Architecture
* `EventClassifierPort` (Abstract protocol supporting dynamic category lists)
* `MockEventClassifier` (Rule-based keyword classifier matching against dynamic categories)
* `GeminiEventClassifier` (Live Gemini API client prompting with tenant's dynamic categories)
* `EventClassificationService` (Orchestrator: queries tenant categories from MongoDB, classifies, and caches category directly on the `Event` document)

---

## 🛠️ 2. File Structure

```text
entry-recommendation-service/
├── app/
│   ├── classification/
│   │   ├── __init__.py
│   │   ├── taxonomy.py              # CategoryDefinition, TenantConfig, EventClassificationResult
│   │   ├── classifier_port.py       # EventClassifierPort protocol
│   │   ├── mock_classifier.py       # Deterministic dynamic matcher
│   │   ├── gemini_classifier.py     # Dynamic Gemini LLM adapter
│   │   └── service.py               # ClassificationService with DB caching
├── tests/
│   └── test_event_classifier.py     # Tests for dynamic categorization & caching
└── plans/
    └── slice-2-event-classifier.md  # This document
```

---

## 🔍 3. Verification & Done Criteria (COMPLETED ✅)

- [x] Dynamic tenant categories defined at runtime (e.g. `chess_club`, `vr_zone`) are classified accurately.
- [x] Fallback to `other` when no tenant categories match.
- [x] Caching works: already classified events are retrieved without re-running LLM.
- [x] All 25 unit tests pass in pytest within 0.29s.
