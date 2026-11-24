from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from .base import PyObjectId

class Event(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    date: datetime
    description: Optional[str] = None
    isActive: bool = True
    category: Optional[str] = None
    time_bucket: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
