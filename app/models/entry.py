from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from .base import PyObjectId

class Entry(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    participantId: PyObjectId
    eventId: PyObjectId
    scannerId: Optional[PyObjectId] = None
    entryTime: datetime = Field(default_factory=datetime.utcnow)
    method: str = "barcode"
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
