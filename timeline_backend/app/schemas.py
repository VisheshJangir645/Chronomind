import uuid
from pydantic import BaseModel, Field
from typing import List, Optional

class TextRequest(BaseModel):
    text: str = Field(..., description="Unstructured historical text to parse")
    base_date: Optional[str] = None

class QueryRequest(BaseModel):
    query: str = Field(..., description="Topic, person, or event to generate timeline for")

class ConfidenceMetrics(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=1.0)
    model_probability: float
    source_agreement: float
    temporal_consistency: float

class ChronoEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., description="Concise event headline")
    description: str = Field(..., description="Full historical narrative")
    date_normalized: str = Field(..., description="ISO-8601 date for sorting")
    raw_date_string: str = Field(default="")
    people: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    causes: List[str] = Field(default_factory=list)
    leads_to: List[str] = Field(default_factory=list)
    confidence: Optional[ConfidenceMetrics] = None
    sources: List[str] = Field(default_factory=lambda: ["Wikipedia"])
    conflict_flag: bool = False
    related_context: Optional[str] = None
    image_url: Optional[str] = None
    key_facts: List[str] = Field(default_factory=list)
    relevance_score: Optional[float] = Field(None, description="0.0-1.0 contextual relevance")
    related_to: Optional[str] = Field(None, description="Title of the causally preceding event")
    embedding: Optional[List[float]] = Field(None, exclude=True)

class TimelineResponse(BaseModel):
    events: List[ChronoEvent]
    topic: Optional[str] = None
    summary: Optional[str] = None
    thumbnail: Optional[str] = None
    images: List[str] = Field(default_factory=list)
