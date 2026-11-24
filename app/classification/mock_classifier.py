from typing import Optional, List
from .classifier_port import EventClassifierPort
from .taxonomy import CategoryDefinition, EventClassificationResult

class MockEventClassifier(EventClassifierPort):
    """
    Deterministic rule-based event classifier matching against dynamic CategoryDefinition objects.
    """

    async def classify_event(
        self,
        name: str,
        description: Optional[str] = None,
        available_categories: Optional[List[CategoryDefinition]] = None
    ) -> EventClassificationResult:
        categories = available_categories or []
        event_text = f"{name or ''} {description or ''}".lower()

        # Score each category based on exact keyword overlap
        best_match: Optional[CategoryDefinition] = None
        best_score = 0

        for cat in categories:
            if not cat.is_active or cat.key == "other":
                continue

            score = 0
            # Check key
            if cat.key.lower() in event_text:
                score += 5

            # Check words from display_name
            for word in cat.display_name.lower().split():
                clean_word = word.strip(",.() ")
                if len(clean_word) >= 3 and clean_word in event_text:
                    score += 3

            # Check words from description
            if cat.description:
                for term in cat.description.lower().split(","):
                    clean_term = term.strip()
                    if clean_term and clean_term in event_text:
                        score += 5
                    else:
                        for word in clean_term.split():
                            clean_word = word.strip(",.() ")
                            if len(clean_word) >= 3 and clean_word in event_text:
                                score += 2

            if score > best_score:
                best_score = score
                best_match = cat

        if best_match and best_score > 0:
            return EventClassificationResult(
                category_key=best_match.key,
                display_name=best_match.display_name,
                confidence=min(0.95, 0.6 + (best_score * 0.1)),
                reasoning=f"Matched dynamic category '{best_match.display_name}' with score {best_score}"
            )

        # Fallback to 'other'
        fallback_cat = next((c for c in categories if c.key == "other"), None)
        return EventClassificationResult(
            category_key=fallback_cat.key if fallback_cat else "other",
            display_name=fallback_cat.display_name if fallback_cat else "אחר",
            confidence=0.5,
            reasoning="No dynamic category matched event details"
        )
