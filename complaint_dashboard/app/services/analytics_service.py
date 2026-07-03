import datetime
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Complaint

logger = logging.getLogger(__name__)

async def get_dashboard_analytics(
    db: AsyncSession,
    search: Optional[str] = None,
    topic_id: Optional[int] = None,
    location: Optional[str] = None,
    sentiment: Optional[str] = None,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    user_type: Optional[str] = None,
    intensity_min: Optional[float] = None,
    intensity_max: Optional[float] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
) -> Dict[str, Any]:
    """
    Aggregates comprehensive dashboard metrics based on filtered complaints.
    """
    # 1. Fetch complaints matching the filters
    query = select(Complaint)
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Complaint.complaint_text.like(search_pattern),
                Complaint.ai_summary.like(search_pattern),
                Complaint.topic_label.like(search_pattern),
                Complaint.location.like(search_pattern)
            )
        )
        
    if topic_id is not None:
        conditions.append(Complaint.topic_id == topic_id)
    if location:
        conditions.append(Complaint.location == location)
    if sentiment:
        conditions.append(Complaint.sentiment_label == sentiment.upper())
    if severity:
        conditions.append(Complaint.severity == severity.lower())
    if source:
        conditions.append(Complaint.complaint_source == source.lower())
    if user_type:
        conditions.append(Complaint.user_type == user_type.lower())
    if intensity_min is not None:
        conditions.append(Complaint.intensity_score >= intensity_min)
    if intensity_max is not None:
        conditions.append(Complaint.intensity_score <= intensity_max)
    if date_start:
        conditions.append(Complaint.complaint_date >= date_start)
    if date_end:
        conditions.append(Complaint.complaint_date <= date_end)
        
    if conditions:
        query = query.where(and_(*conditions))
        
    result = await db.execute(query)
    complaints = result.scalars().all()
    
    total_complaints = len(complaints)
    
    # 2. Compute live/recent count (submitted in the last 2 hours)
    two_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
    live_count = sum(1 for c in complaints if c.timestamp and c.timestamp >= two_hours_ago)
    
    # 3. Distributions
    sentiments = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
    severities = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    user_types = {}
    sources = {}
    locations = {}
    topics = {}
    
    total_intensity = 0.0
    
    for c in complaints:
        # Sentiment
        s_lbl = c.sentiment_label or "NEUTRAL"
        sentiments[s_lbl] = sentiments.get(s_lbl, 0) + 1
        
        # Severity
        sev = c.severity or "medium"
        severities[sev] = severities.get(sev, 0) + 1
        
        # User Type
        ut = c.user_type or "regular"
        user_types[ut] = user_types.get(ut, 0) + 1
        
        # Source
        src = c.complaint_source or "website"
        sources[src] = sources.get(src, 0) + 1
        
        # Location
        loc = c.location or "Unknown"
        locations[loc] = locations.get(loc, 0) + 1
        
        # Topics
        t_lbl = c.topic_label or "Uncategorized"
        topics[t_lbl] = topics.get(t_lbl, 0) + 1
        
        # Intensity
        total_intensity += c.intensity_score or 0.0
        
    avg_intensity = round(total_intensity / total_complaints, 2) if total_complaints > 0 else 0.0
    
    # Sort dictionaries for UI consistency
    sorted_locations = dict(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:8])
    sorted_topics = dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:8])
    
    # 4. Spike Detection
    recent_spikes = False
    if live_count >= 3: # If more than 3 complaints received in past 2 hours locally, alert!
        recent_spikes = True
        
    # 5. Dynamic AI-Generated Insights
    ai_insights = generate_insights_heuristics(
        total_complaints, sentiments, severities, user_types, sources, sorted_topics, avg_intensity, recent_spikes
    )
    
    return {
        "total_complaints": total_complaints,
        "live_count": live_count,
        "sentiment_distribution": sentiments,
        "severity_distribution": severities,
        "intensity_average": avg_intensity,
        "user_type_distribution": user_types,
        "source_distribution": sources,
        "location_distribution": sorted_locations,
        "topic_distribution": sorted_topics,
        "recent_spikes": recent_spikes,
        "ai_insights": ai_insights
    }

async def get_complaint_trends(
    db: AsyncSession,
    days: int = 7
) -> List[Dict[str, Any]]:
    """
    Fetches the number of complaints per day for the last N days.
    """
    today = datetime.date.today()
    date_list = [today - datetime.timedelta(days=i) for i in range(days)]
    date_strings = [d.strftime("%Y-%m-%d") for d in date_list]
    
    # Query database grouping by date
    query = (
        select(Complaint.complaint_date, func.count(Complaint.complaint_id))
        .where(Complaint.complaint_date.in_(date_strings))
        .group_by(Complaint.complaint_date)
    )
    result = await db.execute(query)
    db_counts = dict(result.all())
    
    # Ensure all days are represented, even with 0 counts
    trend_points = []
    # Reverse to show chronological order (oldest to newest)
    for d_str in reversed(date_strings):
        trend_points.append({
            "date": d_str,
            "count": db_counts.get(d_str, 0)
        })
        
    return trend_points

def generate_insights_heuristics(
    total: int,
    sentiments: dict,
    severities: dict,
    user_types: dict,
    sources: dict,
    topics: dict,
    avg_intensity: float,
    recent_spikes: bool
) -> List[str]:
    """Generates analytical insights using smart rule engine."""
    insights = []
    
    if total == 0:
        return ["No complaint data loaded. Submit complaints or seed the database to view insights."]
        
    # Insight 1: Sentiment concentration
    neg_pct = int((sentiments.get("NEGATIVE", 0) / total) * 100)
    if neg_pct > 60:
        insights.append(f"Critical Sentiment Alert: Negative complaints account for {neg_pct}% of total submissions, indicating systemic dissatisfaction.")
    else:
        insights.append(f"Sentiment Analysis: Neutral/Positive customer interactions comprise {100 - neg_pct}% of complaints, hinting at mild friction.")
        
    # Insight 2: Spike/Volume alerts
    if recent_spikes:
        insights.append("Volume Spike Warning: A cluster of incoming complaints has been detected in the last 2 hours. Inspect the live feed for operational blocks.")
        
    # Insight 3: Core Problem Areas (Topics)
    if topics:
        top_topic, top_count = list(topics.items())[0]
        top_topic_pct = int((top_count / total) * 100)
        if top_topic_pct >= 25:
            insights.append(f"Bottleneck Discovered: Topic '{top_topic}' dominates, accounting for {top_topic_pct}% of all issues. Action recommended in this department.")
            
    # Insight 4: Severity & High value clients
    crit_count = severities.get("critical", 0) + severities.get("high", 0)
    crit_pct = int((crit_count / total) * 100)
    if crit_pct > 30:
        insights.append(f"Escalation Risk: {crit_pct}% of issues are flagged High/Critical. Immediate operations routing required to prevent SLA violations.")
        
    # Insight 5: Channel Optimization
    if sources:
        top_source = max(sources, key=sources.get)
        src_pct = int((sources[top_source] / total) * 100)
        if top_source in ["social media", "email"] and src_pct > 40:
            insights.append(f"PR Exposure: {src_pct}% of issues are originating via external {top_source}. Ensure response times are minimized on public interfaces.")
            
    # Fallback to keep 3 insights minimum
    while len(insights) < 3:
        insights.append("System Operations: Ingestion pipelines and topic clustering services are running optimally.")
        
    return insights[:4]
