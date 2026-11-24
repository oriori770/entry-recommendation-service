from typing import Optional, List
from app.models.event import Event
from app.classification.classifier_port import EventClassifierPort
from app.classification.taxonomy import CategoryDefinition, TenantConfig, EventClassificationResult

DEFAULT_CATEGORIES = [
    CategoryDefinition(
        key="football",
        display_name="טורניר כדורגל",
        description="משחקי כדורגל, קט-רגל, ספורט וטורנירים",
        icon="sports_soccer"
    ),
    CategoryDefinition(
        key="torah_lecture",
        display_name="שיעור תורה",
        description="שיעורי גמרא, הלכה, מאמרים ולימוד",
        icon="menu_book"
    ),
    CategoryDefinition(
        key="farbrengen",
        display_name="התוועדות חסידית",
        description="התוועדויות, ימי דפגרא, מלווה מלכה",
        icon="celebration"
    ),
    CategoryDefinition(
        key="prayer",
        display_name="תפילה במניין",
        description="תפילת שחרית, מנחה, מעריב, ותיקין",
        icon="synagogue"
    ),
    CategoryDefinition(
        key="social_gathering",
        display_name="פעילות חברתית",
        description="על האש, טיולים, ימי גיבוש",
        icon="groups"
    ),
    CategoryDefinition(
        key="other",
        display_name="אירוע כללי / אחר",
        description="אירועים שלא שייכים לאחת הקטגוריות הקודמות",
        icon="event"
    )
]

class EventClassificationService:
    """
    Orchestrates dynamic event classification with Multi-Tenant configuration and caching.
    """

    def __init__(self, classifier: EventClassifierPort, db=None):
        self.classifier = classifier
        self.db = db

    async def get_tenant_categories(self, group_id: Optional[str] = None) -> List[CategoryDefinition]:
        """
        Retrieves dynamic categories defined for the tenant from MongoDB.
        Falls back to default organization categories if not explicitly configured in DB.
        """
        if self.db is not None and group_id:
            try:
                doc = await self.db["tenant_configs"].find_one({"group_id": group_id})
                if doc and "categories" in doc:
                    tenant_config = TenantConfig.model_validate(doc)
                    return tenant_config.categories
            except Exception:
                pass

        return DEFAULT_CATEGORIES

    async def get_or_classify_event(self, event: Event, group_id: Optional[str] = None) -> EventClassificationResult:
        # 1. Return cached category if already present on event
        if event.category:
            categories = await self.get_tenant_categories(group_id)
            matched = next((c for c in categories if c.key == event.category), None)
            return EventClassificationResult(
                category_key=event.category,
                display_name=matched.display_name if matched else event.category,
                confidence=1.0,
                reasoning="Cached from event document"
            )

        # 2. Fetch dynamic categories for this event's organization
        available_categories = await self.get_tenant_categories(group_id)

        # 3. Classify dynamically
        result = await self.classifier.classify_event(
            name=event.name,
            description=event.description,
            available_categories=available_categories
        )

        # 4. Update the event object
        event.category = result.category_key

        # 5. Persist to DB if connected
        if self.db is not None and event.id:
            try:
                await self.db["events"].update_one(
                    {"_id": event.id},
                    {"$set": {"category": result.category_key}}
                )
            except Exception:
                pass

        return result
