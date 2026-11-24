from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any
from app.models.base import PyObjectId

class CategoryDefinition(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key: str = Field(description="Unique system key used in statistics, e.g. 'football'")
    display_name: str = Field(description="User-facing label for frontend UI, e.g. 'טורניר כדורגל'")
    description: str = Field(description="Guidelines describing this category for the LLM classifier")
    icon: Optional[str] = Field(default=None, description="UI icon identifier")
    is_active: bool = Field(default=True, description="Whether this category is currently active")

class TenantConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    group_id: str = Field(description="Identifier of event group / organization, e.g. 'temimim'")
    display_name: str = Field(description="Organization display name")
    description: Optional[str] = Field(default=None, description="Organization details")
    categories: List[CategoryDefinition] = Field(default_factory=list, description="Dynamic categories defined for this tenant")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Custom SaaS preferences & configurations")

class EventClassificationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category_key: str = Field(description="System key of the matched category")
    display_name: Optional[str] = Field(default=None, description="Display name for UI")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(default="", description="Reason for matching this category")
