from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List, Protocol
from app.models.event import Event
from .scoring_config import CandidateMatch

class ParticipantRecommendation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    participant_id: str
    participant_name: str
    phone: Optional[str] = None
    city: Optional[str] = None
    group_type: Optional[str] = None
    score: int = Field(ge=0, le=100, description="Normalized compatibility score (0-100)")
    reasoning: str = Field(description="Factual, grounded explanation in Hebrew")
    breakdown: Dict[str, Any] = Field(default_factory=dict)

class AIScorerPort(Protocol):
    async def generate_recommendations(
        self,
        event: Event,
        candidates: List[CandidateMatch]
    ) -> List[ParticipantRecommendation]:
        """
        Ranks, normalizes scores (0-100), and generates grounded Hebrew reasoning.
        """
        ...
