import logging
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.connection import get_db
from app.database.models import Complaint
from app.schemas.complaint import AnalyticsSummary, TrendPoint, TopicDetail
from app.services import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("", response_model=AnalyticsSummary)
async def get_analytics(
    search: Optional[str] = Query(None),
    topic_id: Optional[int] = Query(None),
    location: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    user_type: Optional[str] = Query(None),
    intensity_min: Optional[float] = Query(None),
    intensity_max: Optional[float] = Query(None),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns aggregated analytical summaries of the banking complaints base
    matching query filters.
    """
    try:
        analytics = await analytics_service.get_dashboard_analytics(
            db, search=search, topic_id=topic_id, location=location,
            sentiment=sentiment, severity=severity, source=source,
            user_type=user_type, intensity_min=intensity_min, intensity_max=intensity_max,
            date_start=date_start, date_end=date_end
        )
        return analytics
    except Exception as e:
        logger.error(f"Error fetching dashboard analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load dashboard metrics.")

@router.get("/trends", response_model=List[TrendPoint])
async def get_trends(
    days: int = Query(7, ge=3, le=30, description="Number of days to check"),
    db: AsyncSession = Depends(get_db)
):
    """Fetches a chronological timeline of complaints count per day."""
    try:
        trends = await analytics_service.get_complaint_trends(db, days=days)
        return trends
    except Exception as e:
        logger.error(f"Error fetching trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load daily trends.")

@router.get("/topics", response_model=List[TopicDetail])
async def get_topics_summary(
    db: AsyncSession = Depends(get_db)
):
    """Fetches a list of all dynamically extracted topics with document counts and keywords."""
    try:
        # Group by topic_id and fetch label, keywords, and count
        query = (
            select(
                Complaint.topic_id,
                Complaint.topic_label,
                Complaint.topic_keywords,
                func.count(Complaint.complaint_id)
            )
            .group_by(Complaint.topic_id, Complaint.topic_label, Complaint.topic_keywords)
            .order_by(Complaint.topic_id.asc())
        )
        result = await db.execute(query)
        rows = result.all()
        
        topics_list = []
        for row in rows:
            t_id, t_label, kw_str, count = row
            
            # De-serialize keywords JSON list
            keywords = []
            if kw_str:
                try:
                    keywords = json.loads(kw_str)
                except Exception:
                    keywords = [kw_str]
                    
            topics_list.append({
                "topic_id": t_id,
                "topic_label": t_label,
                "keywords": keywords,
                "complaint_count": count
            })
            
        return topics_list
    except Exception as e:
        logger.error(f"Error fetching topics summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load topics summary.")
