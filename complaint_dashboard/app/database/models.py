import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Date, Time
from app.database.connection import Base

class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(String(36), primary_key=True, index=True)
    complaint_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=True)
    complaint_date = Column(String(10), nullable=True)  # YYYY-MM-DD format
    complaint_time = Column(String(8), nullable=True)   # HH:MM:SS format
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    location = Column(String(100), nullable=True)
    user_type = Column(String(50), nullable=False)      # premium, regular, business, senior citizen, student
    complaint_source = Column(String(50), nullable=False)  # offline, mobile app, website, email, social media
    
    # Store embedding array as a JSON string to avoid external vector db dependencies
    embedding_vector_reference = Column(Text, nullable=True)
    
    topic_id = Column(Integer, default=-1, nullable=False)
    topic_label = Column(String(100), default="Uncategorized", nullable=False)
    topic_keywords = Column(Text, nullable=True)  # JSON-serialized list
    
    sentiment_label = Column(String(20), nullable=True)  # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score = Column(Float, nullable=True)
    intensity_score = Column(Float, nullable=True)      # 0 to 1
    severity = Column(String(20), nullable=True)         # low, medium, high, critical
    
    # AI Summary and Routing
    ai_summary = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    solving_steps = Column(Text, nullable=True)          # JSON-serialized list
    recommended_department = Column(String(100), nullable=True)
    escalation_priority = Column(String(20), nullable=True) # low, medium, high, immediate
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    def to_dict(self):
        """Helper to serialize model database fields to dictionary."""
        return {
            "complaint_id": self.complaint_id,
            "complaint_text": self.complaint_text,
            "cleaned_text": self.cleaned_text,
            "complaint_date": self.complaint_date,
            "complaint_time": self.complaint_time,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "location": self.location,
            "user_type": self.user_type,
            "complaint_source": self.complaint_source,
            "topic_id": self.topic_id,
            "topic_label": self.topic_label,
            "topic_keywords": self.topic_keywords,
            "sentiment_label": self.sentiment_label,
            "sentiment_score": self.sentiment_score,
            "intensity_score": self.intensity_score,
            "severity": self.severity,
            "ai_summary": self.ai_summary,
            "root_cause": self.root_cause,
            "solving_steps": self.solving_steps,
            "recommended_department": self.recommended_department,
            "escalation_priority": self.escalation_priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
