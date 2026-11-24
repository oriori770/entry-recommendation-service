from typing import Protocol, Optional, List
from .taxonomy import CategoryDefinition, EventClassificationResult

class EventClassifierPort(Protocol):
    async def classify_event(
        self,
        name: str,
        description: Optional[str] = None,
        available_categories: Optional[List[CategoryDefinition]] = None
    ) -> EventClassificationResult:
        """
        Classifies an event against a dynamic list of CategoryDefinition objects.
        """
        ...
