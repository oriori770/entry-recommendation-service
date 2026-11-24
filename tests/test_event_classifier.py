import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from app.models.event import Event
from app.classification.taxonomy import CategoryDefinition
from app.classification.mock_classifier import MockEventClassifier
from app.classification.service import EventClassificationService, DEFAULT_CATEGORIES

@pytest.fixture
def classifier():
    return MockEventClassifier()

@pytest.mark.asyncio
async def test_classify_sports_event_dynamic(classifier):
    res = await classifier.classify_event(
        name="טורניר קט רגל ישיבתי",
        description="משחק גמר באולם",
        available_categories=DEFAULT_CATEGORIES
    )
    assert res.category_key == "football"
    assert res.display_name == "טורניר כדורגל"
    assert res.confidence >= 0.9

@pytest.mark.asyncio
async def test_classify_custom_saas_tenant_categories(classifier):
    # Custom tenant categories defined completely at runtime
    custom_categories = [
        CategoryDefinition(
            key="vr_zone",
            display_name="מתחם מציאות מדומה",
            description="משחקי VR, משקפי מציאות מדומה, סימולטורים"
        ),
        CategoryDefinition(
            key="chess_club",
            display_name="מועדון שחמט",
            description="משחקי שחמט, תחרויות שח, אסטרטגיה"
        )
    ]

    res = await classifier.classify_event(
        name="תחרות שחמט נושאת פרסים",
        description="משחקי חשיבה בלובי",
        available_categories=custom_categories
    )
    assert res.category_key == "chess_club"
    assert res.display_name == "מועדון שחמט"

@pytest.mark.asyncio
async def test_classify_unknown_event_falls_back_to_other(classifier):
    res = await classifier.classify_event(
        name="אירוע ללא שם מוכר",
        description="פרטים נוספים ימסרו בהמשך",
        available_categories=DEFAULT_CATEGORIES
    )
    assert res.category_key == "other"

@pytest.mark.asyncio
async def test_classification_service_caching():
    mock_port = AsyncMock()
    service = EventClassificationService(classifier=mock_port)

    # Event already has category -> should NOT call classifier
    event = Event(
        name="טורניר כדורגל",
        date=datetime.now(),
        category="football"
    )
    result = await service.get_or_classify_event(event)
    assert result.category_key == "football"
    mock_port.classify_event.assert_not_called()

@pytest.mark.asyncio
async def test_classification_service_invokes_and_caches_on_event(classifier):
    service = EventClassificationService(classifier=classifier)
    event = Event(
        name="התוועדות יט כסלו",
        date=datetime.now()
    )
    assert event.category is None

    result = await service.get_or_classify_event(event)
    assert result.category_key == "farbrengen"
    assert result.display_name == "התוועדות חסידית"
    # Check that event object was updated
    assert event.category == "farbrengen"
