import pytest
from datetime import datetime, timedelta
from bson import ObjectId
from app.models.participant import Participant
from app.models.event import Event
from app.models.entry import Entry
from app.profiles.engine import ProfileEngine
from app.profiles.backfill import BackfillService
from app.classification.mock_classifier import MockEventClassifier
from app.classification.service import EventClassificationService

@pytest.fixture
def base_participant():
    return Participant(
        id=ObjectId("507f1f77bcf86cd799439011"),
        name="ישראל",
        family="ישראלי",
        phone="0501234567",
        groupType="temimim"
    )

def test_atomic_entry_update_generation(base_participant):
    event = Event(
        id=ObjectId("507f1f77bcf86cd799439022"),
        name="טורניר כדורגל",
        date=datetime(2026, 11, 26, 18, 0, 0),  # Thursday 18:00
        category="football"
    )
    # Entry arrived 10m before event start -> on time, Thursday, evening_17_21
    entry = Entry(
        participantId=base_participant.id,
        eventId=event.id,
        entryTime=datetime(2026, 11, 26, 17, 50, 0)
    )

    update_op = ProfileEngine.build_atomic_entry_update(base_participant, event, entry)

    # Verify operators
    assert update_op["$inc"]["stats.categories.football"] == 1
    assert update_op["$inc"]["stats.time_buckets.evening_17_21"] == 1
    assert update_op["$inc"]["stats.days_of_week.thursday"] == 1
    assert update_op["$inc"]["stats.punctuality.on_time"] == 1
    assert update_op["$inc"]["stats.total_attendances"] == 1
    assert update_op["$set"]["stats.streak.current_streak"] == 1
    assert update_op["$set"]["stats.streak.longest_streak"] == 1

def test_streak_continuation_and_record(base_participant):
    event1 = Event(
        name="אירוע 1",
        date=datetime(2026, 11, 20, 18, 0, 0),
        category="football"
    )
    entry1 = Entry(
        participantId=base_participant.id,
        eventId=ObjectId(),
        entryTime=datetime(2026, 11, 20, 18, 0, 0)
    )
    op1 = ProfileEngine.build_atomic_entry_update(base_participant, event1, entry1)
    ProfileEngine.apply_update_in_memory(base_participant, op1)

    assert base_participant.stats.streak.current_streak == 1
    assert base_participant.stats.streak.longest_streak == 1

    # Second entry 2 days later -> streak continues
    event2 = Event(
        name="אירוע 2",
        date=datetime(2026, 11, 22, 18, 0, 0),
        category="football"
    )
    entry2 = Entry(
        participantId=base_participant.id,
        eventId=ObjectId(),
        entryTime=datetime(2026, 11, 22, 18, 0, 0)
    )
    op2 = ProfileEngine.build_atomic_entry_update(base_participant, event2, entry2)
    ProfileEngine.apply_update_in_memory(base_participant, op2)

    assert base_participant.stats.streak.current_streak == 2
    assert base_participant.stats.streak.longest_streak == 2

    # Third entry 20 days later -> streak resets to 1, but longest remains 2
    event3 = Event(
        name="אירוע 3",
        date=datetime(2026, 12, 12, 18, 0, 0),
        category="shiur"
    )
    entry3 = Entry(
        participantId=base_participant.id,
        eventId=ObjectId(),
        entryTime=datetime(2026, 12, 12, 18, 0, 0)
    )
    op3 = ProfileEngine.build_atomic_entry_update(base_participant, event3, entry3)
    ProfileEngine.apply_update_in_memory(base_participant, op3)

    assert base_participant.stats.streak.current_streak == 1
    assert base_participant.stats.streak.longest_streak == 2
    assert base_participant.stats.total_attendances == 3

@pytest.mark.asyncio
async def test_backfill_replay_single_participant(base_participant):
    classifier = MockEventClassifier()
    classification_service = EventClassificationService(classifier=classifier)
    backfill_service = BackfillService(classification_service=classification_service)

    ev1_id = ObjectId()
    ev2_id = ObjectId()

    events_by_id = {
        str(ev1_id): Event(id=ev1_id, name="טורניר קט רגל", date=datetime(2026, 10, 1, 18, 0, 0)),
        str(ev2_id): Event(id=ev2_id, name="התוועדות חסידית", date=datetime(2026, 10, 4, 21, 30, 0))
    }

    entries = [
        Entry(participantId=base_participant.id, eventId=ev1_id, entryTime=datetime(2026, 10, 1, 18, 5, 0)),
        Entry(participantId=base_participant.id, eventId=ev2_id, entryTime=datetime(2026, 10, 4, 22, 0, 0)) # Late
    ]

    updated_participant = await backfill_service.replay_participant_entries(
        base_participant, entries, events_by_id
    )

    assert updated_participant.stats.total_attendances == 2
    assert updated_participant.stats.categories["football"] == 1
    assert updated_participant.stats.categories["farbrengen"] == 1
    assert updated_participant.stats.punctuality.on_time == 1
    assert updated_participant.stats.punctuality.late == 1
    assert updated_participant.stats.streak.current_streak == 2
