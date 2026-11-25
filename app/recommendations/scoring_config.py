from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional

class ScoringWeights(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    weight_category: float = Field(default=40.0, description="Weight for matching event category counter")
    weight_time_bucket: float = Field(default=25.0, description="Weight for matching diurnal time slot counter")
    weight_day_of_week: float = Field(default=15.0, description="Weight for matching day of week counter")
    weight_streak: float = Field(default=10.0, description="Weight multiplier for active streak")
    weight_punctuality: float = Field(default=10.0, description="Weight for on-time punctuality ratio")

class CandidateMatch(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    participant_id: str
    participant_name: str
    phone: Optional[str] = None
    city: Optional[str] = None
    group_type: Optional[str] = None
    total_score: float
    breakdown: Dict[str, Any] = Field(default_factory=dict, description="Factual metrics justifying the match")
