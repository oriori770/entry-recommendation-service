import pytest
from datetime import datetime
from bson import ObjectId
from app.models.participant import Participant
from app.models.event import Event
from app.recommendations.scoring_config import ScoringWeights
from app.recommendations.retrieval import MongoCandidateRetriever

@pytest.fixture
def retriever():
    return MongoCandidateRetriever()

@pytest.fixture
def sample_candidates():
    # Candidate A: Heavy football player, evening enthusiast, Thursday regular
    p_a = Participant(
        id=ObjectId("507f1f77bcf86cd799439011"),
        name="יוסי",
        family="כהן",
        phone="0501111111",
        groupType="temimim",
        isApproved=True,
        stats={
            "categories": {"football": 10, "shiur": 1},
            "time_buckets": {"evening_17_21": 8, "morning_06_12": 1},
            "days_of_week": {"thursday": 7, "sunday": 2},
            "punctuality": {"on_time": 9, "late": 1},
            "streak": {"current_streak": 4, "longest_streak": 5},
            "total_attendances": 11
        }
    )

    # Candidate B: Shiur/Torah regular, morning enthusiast, rarely plays football
    p_b = Participant(
        id=ObjectId("507f1f77bcf86cd799439022"),
        name="אברהם",
        family="לוי",
        phone="0502222222",
        groupType="temimim",
        isApproved=True,
        stats={
            "categories": {"football": 1, "torah_lecture": 15},
            "time_buckets": {"morning_06_12": 14, "evening_17_21": 1},
            "days_of_week": {"sunday": 5, "tuesday": 5, "thursday": 1},
            "punctuality": {"on_time": 15, "late": 0},
            "streak": {"current_streak": 6, "longest_streak": 8},
            "total_attendances": 16
        }
    )

    # Candidate C: Unapproved participant (should be skipped)
    p_c = Participant(
        id=ObjectId("507f1f77bcf86cd799439033"),
        name="דניאל",
        family="ישראלי",
        phone="0503333333",
        groupType="temimim",
        isApproved=False,
        stats={"categories": {"football": 20}}
    )

    return [p_a, p_b, p_c]

def test_football_event_ranks_football_player_highest(retriever, sample_candidates):
    event = Event(
        name="טורניר כדורגל ערב",
        date=datetime(2026, 11, 26, 19, 0, 0),  # Thursday 19:00 (evening_17_21)
        category="football"
    )

    ranked = retriever.rank_candidates(sample_candidates, event, top_k=5)

    # Only approved candidates returned (A and B)
    assert len(ranked) == 2

    # Candidate A must score significantly higher than Candidate B for football
    top_candidate = ranked[0]
    assert top_candidate.participant_id == str(sample_candidates[0].id)
    assert top_candidate.participant_name == "יוסי כהן"
    assert top_candidate.total_score > ranked[1].total_score
    assert top_candidate.breakdown["category_attendances"] == 10
    assert top_candidate.breakdown["time_bucket"] == "evening_17_21"

def test_torah_lecture_ranks_torah_student_highest(retriever, sample_candidates):
    event = Event(
        name="שיעור גמרא בוקר",
        date=datetime(2026, 11, 22, 9, 0, 0),  # Sunday 09:00 (morning_06_12)
        category="torah_lecture"
    )

    ranked = retriever.rank_candidates(sample_candidates, event, top_k=5)

    assert len(ranked) == 2
    # Candidate B must score higher for morning Torah lecture
    assert ranked[0].participant_id == str(sample_candidates[1].id)
    assert ranked[0].participant_name == "אברהם לוי"
    assert ranked[0].total_score > ranked[1].total_score

def test_top_k_limits_results(retriever, sample_candidates):
    event = Event(
        name="אירוע כללי",
        date=datetime.now(),
        category="other"
    )
    # Request only top 1
    ranked = retriever.rank_candidates(sample_candidates, event, top_k=1)
    assert len(ranked) == 1
