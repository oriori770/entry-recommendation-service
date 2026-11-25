from typing import List, Optional, Dict, Any
from app.models.participant import Participant
from app.models.event import Event
from app.classification.time_buckets import get_time_bucket
from app.classification.temporal_features import get_day_of_week
from .scoring_config import ScoringWeights, CandidateMatch

class MongoCandidateRetriever:
    """
    Ranks participants deterministically based on behavioral counters matching event attributes.
    """

    def __init__(self, db=None, default_weights: Optional[ScoringWeights] = None):
        self.db = db
        self.weights = default_weights or ScoringWeights()

    def score_participant(
        self,
        participant: Participant,
        event: Event,
        weights: Optional[ScoringWeights] = None
    ) -> CandidateMatch:
        w = weights or self.weights
        stats = participant.stats

        cat_key = event.category or "other"
        tb_key = event.time_bucket or get_time_bucket(event.date)
        dow_key = get_day_of_week(event.date)

        # 1. Category score
        cat_count = stats.categories.get(cat_key, 0)
        cat_score = cat_count * w.weight_category

        # 2. Time bucket score
        tb_count = stats.time_buckets.get(tb_key, 0)
        tb_score = tb_count * w.weight_time_bucket

        # 3. Day of week score
        dow_count = stats.days_of_week.get(dow_key, 0)
        dow_score = dow_count * w.weight_day_of_week

        # 4. Streak score
        streak_val = stats.streak.current_streak
        streak_score = streak_val * w.weight_streak

        # 5. Punctuality score
        total_p = stats.punctuality.on_time + stats.punctuality.late
        punct_ratio = (stats.punctuality.on_time / total_p) if total_p > 0 else 0.5
        punct_score = punct_ratio * w.weight_punctuality

        total_score = round(cat_score + tb_score + dow_score + streak_score + punct_score, 2)

        return CandidateMatch(
            participant_id=str(participant.id) if participant.id else "",
            participant_name=f"{participant.name} {participant.family}",
            phone=participant.phone,
            city=participant.city,
            group_type=participant.groupType,
            total_score=total_score,
            breakdown={
                "category_key": cat_key,
                "category_attendances": cat_count,
                "time_bucket": tb_key,
                "time_bucket_attendances": tb_count,
                "day_of_week": dow_key,
                "day_of_week_attendances": dow_count,
                "current_streak": streak_val,
                "on_time_ratio": round(punct_ratio, 2),
                "total_historical_attendances": stats.total_attendances
            }
        )

    def rank_candidates(
        self,
        participants: List[Participant],
        event: Event,
        top_k: int = 10,
        weights: Optional[ScoringWeights] = None,
        min_score: float = 0.0
    ) -> List[CandidateMatch]:
        """
        Ranks in-memory list of participants against an event.
        """
        matches = [
            self.score_participant(p, event, weights)
            for p in participants
            if p.isApproved
        ]
        # Filter by min_score
        filtered = [m for m in matches if m.total_score >= min_score]
        # Sort descending by score
        sorted_matches = sorted(filtered, key=lambda m: m.total_score, reverse=True)
        return sorted_matches[:top_k]

    async def get_top_candidates_from_db(
        self,
        event: Event,
        group_type: Optional[str] = None,
        top_k: int = 10,
        weights: Optional[ScoringWeights] = None
    ) -> List[CandidateMatch]:
        """
        Queries approved participants from MongoDB, scores and returns Top-K.
        """
        if self.db is None:
            return []

        query: Dict[str, Any] = {"isApproved": True}
        if group_type:
            query["groupType"] = group_type

        cursor = self.db["participants"].find(query)
        participants = []
        async for doc in cursor:
            participants.append(Participant.model_validate(doc))

        return self.rank_candidates(participants, event, top_k=top_k, weights=weights)
