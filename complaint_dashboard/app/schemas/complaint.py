from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any
from datetime import datetime, date, time

class ComplaintCreate(BaseModel):
    complaint_text: str = Field(..., min_length=5, description="The text content of the banking complaint")
    complaint_date: Optional[str] = Field(None, description="Date of the complaint in YYYY-MM-DD format")
    complaint_time: Optional[str] = Field(None, description="Time of the complaint in HH:MM:SS format")
    location: Optional[str] = Field("Unknown", description="Branch location, ATM identifier, or city")
    user_type: str = Field(..., description="Type of user: premium, regular, business, senior citizen, student")
    complaint_source: str = Field(..., description="Source: offline, mobile app, website, email, social media")

    @field_validator("user_type")
    @classmethod
    def validate_user_type(cls, value: str) -> str:
        valid_types = {"premium", "regular", "business", "senior citizen", "student"}
        val_lower = value.lower().strip()
        if val_lower not in valid_types:
            raise ValueError(f"user_type must be one of {valid_types}")
        return val_lower

    @field_validator("complaint_source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        valid_sources = {"offline", "mobile app", "website", "email", "social media"}
        val_lower = value.lower().strip()
        if val_lower not in valid_sources:
            raise ValueError(f"complaint_source must be one of {valid_sources}")
        return val_lower

class ComplaintResponse(BaseModel):
    complaint_id: str
    complaint_text: str
    cleaned_text: Optional[str] = None
    complaint_date: Optional[str] = None
    complaint_time: Optional[str] = None
    timestamp: datetime
    location: Optional[str] = None
    user_type: str
    complaint_source: str
    topic_id: int
    topic_label: str
    topic_keywords: Optional[str] = None  # JSON string or list depending on conversion
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    intensity_score: Optional[float] = None
    severity: Optional[str] = None
    ai_summary: Optional[str] = None
    root_cause: Optional[str] = None
    solving_steps: Optional[str] = None  # JSON string
    recommended_department: Optional[str] = None
    escalation_priority: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedComplaints(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    items: List[ComplaintResponse]

class TopicDetail(BaseModel):
    topic_id: int
    topic_label: str
    keywords: List[str]
    complaint_count: int

class TrendPoint(BaseModel):
    date: str
    count: int

class AnalyticsSummary(BaseModel):
    total_complaints: int
    live_count: int
    sentiment_distribution: dict
    severity_distribution: dict
    intensity_average: float
    user_type_distribution: dict
    source_distribution: dict
    topic_distribution: dict
    location_distribution: dict
    recent_spikes: bool
    ai_insights: List[str]

