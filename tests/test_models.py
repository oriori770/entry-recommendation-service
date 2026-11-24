from bson import ObjectId
from datetime import datetime
from app.models import Participant, Event, Entry, ParticipantStats

def test_participant_parsing_from_mongo_doc(sample_participant_doc):
    participant = Participant.model_validate(sample_participant_doc)
    assert str(participant.id) == "507f1f77bcf86cd799439011"
    assert participant.name == "ישראל"
    assert participant.family == "ישראלי"
    assert participant.stats.total_attendances == 0
    assert participant.stats.categories == {}
    assert participant.stats.days_of_week == {}
    assert participant.stats.punctuality.on_time == 0
    assert participant.stats.streak.current_streak == 0

def test_participant_with_behavioral_stats():
    doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "מנדי",
        "family": "כהן",
        "phone": "0529998877",
        "groupType": "temimim",
        "isApproved": True,
        "stats": {
            "categories": {"football": 5, "farbrengen": 3},
            "time_buckets": {"evening_17_21": 6, "night_21_06": 2},
            "days_of_week": {"thursday": 5, "sunday": 3},
            "punctuality": {"on_time": 7, "late": 1},
            "streak": {"current_streak": 4, "longest_streak": 6},
            "total_attendances": 8,
            "last_active": datetime(2026, 11, 20, 20, 0, 0)
        }
    }
    p = Participant.model_validate(doc)
    assert p.stats.total_attendances == 8
    assert p.stats.categories["football"] == 5
    assert p.stats.time_buckets["evening_17_21"] == 6
    assert p.stats.days_of_week["thursday"] == 5
    assert p.stats.punctuality.on_time == 7
    assert p.stats.punctuality.late == 1
    assert p.stats.streak.current_streak == 4

def test_event_parsing_and_enrichment(sample_event_doc):
    event = Event.model_validate(sample_event_doc)
    assert str(event.id) == "507f1f77bcf86cd799439022"
    assert event.name == "טורניר קט-רגל"
    assert event.isActive is True

    # Test event enrichment
    event.category = "sports_football"
    event.time_bucket = "evening_17_21"
    assert event.category == "sports_football"
    assert event.time_bucket == "evening_17_21"

def test_entry_parsing(sample_entry_doc):
    entry = Entry.model_validate(sample_entry_doc)
    assert str(entry.id) == "507f1f77bcf86cd799439033"
    assert str(entry.participantId) == "507f1f77bcf86cd799439011"
    assert str(entry.eventId) == "507f1f77bcf86cd799439022"
    assert entry.method == "barcode"
