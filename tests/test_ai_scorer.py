import pytest
from datetime import datetime
from app.models.event import Event
from app.recommendations.scoring_config import CandidateMatch
from app.recommendations.ai_scorer_mock import MockAIScorer
from app.recommendations.ai_scorer_llm import LLMAIScorer

@pytest.fixture
def sample_event():
    return Event(
        name="טורניר כדורגל ערב",
        date=datetime(2026, 11, 26, 19, 0, 0),
        category="football",
        time_bucket="evening_17_21"
    )

@pytest.fixture
def sample_candidates():
    return [
        CandidateMatch(
            participant_id="part_1",
            participant_name="יוסי כהן",
            total_score=680.0,
            breakdown={
                "category_attendances": 10,
                "time_bucket_attendances": 8,
                "day_of_week_attendances": 7,
                "current_streak": 4
            }
        ),
        CandidateMatch(
            participant_id="part_2",
            participant_name="אברהם לוי",
            total_score=120.0,
            breakdown={
                "category_attendances": 1,
                "time_bucket_attendances": 2,
                "day_of_week_attendances": 1,
                "current_streak": 0
            }
        )
    ]

@pytest.mark.asyncio
async def test_mock_scorer_generates_grounded_hebrew_reasoning(sample_event, sample_candidates):
    scorer = MockAIScorer()
    recs = await scorer.generate_recommendations(sample_event, sample_candidates)

    assert len(recs) == 2

    top = recs[0]
    assert top.participant_id == "part_1"
    assert top.score >= 90  # Normalized relative score
    assert "השתתף ב-10 אירועים" in top.reasoning
    assert "רצף נוכחות של 4" in top.reasoning

    second = recs[1]
    assert second.participant_id == "part_2"
    assert second.score < top.score
    assert "השתתף ב-1 אירועים" in second.reasoning

@pytest.mark.asyncio
async def test_llm_scorer_fallback_to_mock_on_mock_provider(sample_event, sample_candidates):
    scorer = LLMAIScorer(provider="mock")
    recs = await scorer.generate_recommendations(sample_event, sample_candidates)

    assert len(recs) == 2
    assert 0 <= recs[0].score <= 100
    assert len(recs[0].reasoning) > 0

@pytest.mark.asyncio
async def test_scorer_handles_empty_candidates(sample_event):
    scorer = MockAIScorer()
    recs = await scorer.generate_recommendations(sample_event, [])
    assert recs == []
