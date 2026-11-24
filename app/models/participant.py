from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from .base import PyObjectId
from .stats import ParticipantStats

class Participant(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    family: str
    barcode: Optional[str] = None
    phone: str
    city: Optional[str] = None
    groupType: str
    isApproved: bool = False
    stats: ParticipantStats = Field(default_factory=ParticipantStats)
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
