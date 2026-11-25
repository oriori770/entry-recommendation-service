from typing import List
from app.models.event import Event
from .scoring_config import CandidateMatch
from .ai_scorer_port import AIScorerPort, ParticipantRecommendation

class MockAIScorer(AIScorerPort):
    """
    Deterministic template-based reasoner for offline testing without LLM API costs.
    """

    async def generate_recommendations(
        self,
        event: Event,
        candidates: List[CandidateMatch]
    ) -> List[ParticipantRecommendation]:
        if not candidates:
            return []

        # Find max raw score for normalization
        max_raw = max((c.total_score for c in candidates), default=1.0)
        if max_raw <= 0:
            max_raw = 1.0

        recommendations: List[ParticipantRecommendation] = []

        for c in candidates:
            # Normalize to 60-99 scale based on relative score
            norm_score = int(min(99, max(50, (c.total_score / max_raw) * 95)))

            b = c.breakdown
            cat_count = b.get("category_attendances", 0)
            tb_count = b.get("time_bucket_attendances", 0)
            dow_count = b.get("day_of_week_attendances", 0)
            streak = b.get("current_streak", 0)

            # Build grounded explanation
            reasons = []
            if cat_count > 0:
                reasons.append(f"השתתף ב-{cat_count} אירועים מסוג זה בעבר")
            if tb_count > 0:
                reasons.append(f"פעיל באופן קבוע בשעות אלו ({tb_count} פעמים)")
            if dow_count > 0:
                reasons.append(f"נכח ב-{dow_count} אירועים ביום זה בשבוע")
            if streak >= 2:
                reasons.append(f"נמצא ברצף נוכחות של {streak} אירועים")

            reason_str = "; ".join(reasons) if reasons else "הומלץ על בסיס רמת פעילות כללית במערכת"

            recommendations.append(
                ParticipantRecommendation(
                    participant_id=c.participant_id,
                    participant_name=c.participant_name,
                    phone=c.phone,
                    city=c.city,
                    group_type=c.group_type,
                    score=norm_score,
                    reasoning=reason_str,
                    breakdown=b
                )
            )

        # Sort descending by score
        return sorted(recommendations, key=lambda r: r.score, reverse=True)
