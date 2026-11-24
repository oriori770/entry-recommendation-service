# 📋 Slice 2: Dynamic Event Classifier & Configurable Taxonomy

> **Goal:** Build the event classification engine capable of mapping event names and descriptions to standard categories and time buckets using an LLM, where category definitions and taxonomies are dynamically loaded from configuration files (or per user/tenant/organization in future phases) rather than hardcoded in static Enums.

---

## 🎯 1. Frame (Requirements & Scope)

1. **File-Driven Configurable Taxonomy:**
   - Taxonomies (categories, labels, descriptions, and keywords) must not be locked into hardcoded Python Enums.
   - Core taxonomy is loaded from an external structured file (e.g. `config/categories.yaml` or `config/categories.json`).
   - Architecture prepared for multi-tenant / user group overrides:
     - Default taxonomy file: `config/categories.default.yaml`
     - Extensible interface: `CategoryRepository` (supports loading from local YAML/JSON file now, and dynamic database / tenant settings in future phases).

2. **Structured LLM Output:**
   - Output must match a strict schema validated via Pydantic:
     - `category_id`: The matching identifier from the active taxonomy.
     - `confidence`: Confidence score (`0.0` - `1.0`).
     - `extracted_keywords`: List of keywords extracted from event name and description.
     - `reasoning`: Brief explanation of the assignment.
     - `time_bucket`: Calculated or inferred time bucket identifier.

3. **Prompt Generation with Dynamic Taxonomy (PCTCO Framework):**
   - The LLM prompt dynamically injects the available categories and their descriptions loaded from the config.
   - Strict instructions forbidding hallucinated categories outside the provided list.

4. **Caching & Efficiency:**
   - In-memory cache (keyed by tenant/group + hash of `event_name` + `event_description`) to prevent redundant LLM invocations and token costs.

5. **Resilience & Testing:**
   - Rule-based deterministic fallback when LLM is unreachable or fails schema validation.
   - `MockEventClassifier` for deterministic test suites without requiring live API keys.

---

## 🛠️ 2. Plan (File Structure & Architecture)

```text
entry-recommendation-service/
├── config/
│   └── categories.default.yaml      # File-based core taxonomy definitions
├── app/
│   ├── classification/
│   │   ├── __init__.py
│   │   ├── taxonomy.py              # TaxonomyLoader & CategoryRepository (file-based & tenant-ready)
│   │   ├── schemas.py               # Dynamic CategoryConfig, ClassificationResult
│   │   ├── prompts.py               # Prompt templates dynamically populated with taxonomy
│   │   ├── cache.py                 # Fast in-memory caching layer
│   │   ├── classifier.py            # BaseEventClassifier, LLMEventClassifier, MockEventClassifier
│   │   └── fallback.py             # Rule-based fallback classifier
└── tests/
    ├── test_taxonomy_loader.py      # Verifies loading, parsing, and custom file overrides
    └── test_slice2_classifier.py    # Unit & integration tests for event classification
```

---

## 📝 3. Detailed Component Specifications

### A. Taxonomy Configuration File (`config/categories.default.yaml`)
```yaml
version: "1.0"
default_category: "general"
categories:
  - id: "sports"
    label: "ספורט ופעילות גופנית"
    description: "טורנירי כדורגל, כדורסל, פעילויות ספורטיביות ומשחקים תחרותיים"
    keywords: ["כדורגל", "כדורסל", "טורניר", "משחק", "אימון"]

  - id: "torah_study"
    label: "לימוד תורה ושיעורים"
    description: "שיעורי תורה, הלכה, גמרא, חברותות וסדרי לימוד"
    keywords: ["שיעור", "דף יומי", "גמרא", "הלכה", "חברותא", "לימוד"]

  - id: "farbrengen_chassidus"
    label: "התוועדויות וחסידות"
    description: "התוועדויות חסידיות, מועדים מיוחדים ושיעורי תורת החסידות"
    keywords: ["התוועדות", "חסידות", "מאמר", "כסלו", "יומא דפגרא"]

  - id: "social_gathering"
    label: "מפגשים חברתיים וגיבוש"
    description: "ערבי גיבוש, מלווה מלכה, סעודות משותפות ואירועי חברה"
    keywords: ["גיבוש", "מלווה מלכה", "סעודה", "על האש", "מפגש"]

  - id: "prayer"
    label: "תפילות ומניינים"
    description: "תפילות מיוחדות, מניינים מוקדמים או אירועי תפילה מרכזיים"
    keywords: ["תפילה", "מניין", "סליחות", "שחרית", "מנחה", "ערבית"]

  - id: "general"
    label: "כללי"
    description: "כל אירוע שאינו תואם באופן מובהק לאחת הקטגוריות הקודמות"
    keywords: []
```

### B. Dynamic Taxonomy Repository (`taxonomy.py`)
```python
class CategoryDefinition(BaseModel):
    id: str
    label: str
    description: str
    keywords: List[str] = Field(default_factory=list)

class TaxonomyConfig(BaseModel):
    version: str
    default_category: str
    categories: List[CategoryDefinition]

    def get_category_ids(self) -> List[str]:
        return [c.id for c in self.categories]

    def format_for_prompt(self) -> str:
        """Formats category list and descriptions for the LLM system prompt."""
        return "\n".join([f"- {c.id}: {c.label} ({c.description})" for c in self.categories])

class TaxonomyRepository:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self._cache: Dict[str, TaxonomyConfig] = {}

    def get_taxonomy(self, tenant_id: Optional[str] = None) -> TaxonomyConfig:
        """
        Loads user/tenant specific configuration file if present,
        otherwise falls back to default taxonomy.
        """
        key = tenant_id or "default"
        if key in self._cache:
            return self._cache[key]

        # File lookup: categories.{tenant_id}.yaml or categories.default.yaml
        file_path = self.config_dir / f"categories.{key}.yaml"
        if not file_path.exists():
            file_path = self.config_dir / "categories.default.yaml"

        loaded = self._load_from_file(file_path)
        self._cache[key] = loaded
        return loaded
```

### C. Classifier Interface (`classifier.py`)
```python
class BaseEventClassifier(ABC):
    @abstractmethod
    async def classify(
        self,
        name: str,
        description: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> EventClassificationResult:
        pass
```

---

## 🔍 4. Verification & Definition of Done

* [ ] Taxonomy is read dynamically from the YAML configuration file; changing the YAML updates classification without editing Python code.
* [ ] Support for custom tenant configuration files (e.g. `categories.tenant_123.yaml`) returning custom category lists.
* [ ] Schema guarantees that `category_id` returned by the LLM always exists in the active taxonomy (or defaults to `default_category`).
* [ ] In-memory caching works across multiple requests with identical event details.
* [ ] Mock classifier allows 100% test coverage offline without external API dependencies.
* [ ] All tests run and pass cleanly via `pytest tests/test_taxonomy_loader.py tests/test_slice2_classifier.py`.
