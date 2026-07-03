import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Response
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.complaint import ComplaintCreate, ComplaintResponse, PaginatedComplaints
from app.services import complaint_service
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

@router.post("", response_model=ComplaintResponse, status_code=201)
async def submit_complaint(
    payload: ComplaintCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a new customer complaint.
    Processes text via AI pipeline, stores to SQLite database, and broadcasts to live dashboards.
    """
    try:
        # Create and run AI pipeline
        db_complaint = await complaint_service.create_complaint(db, payload)
        
        # Format response data
        response_data = db_complaint.to_dict()
        
        # Broadcast to WebSocket dashboard connections in background
        background_tasks.add_task(
            manager.broadcast,
            {"event": "new_complaint", "data": response_data}
        )
        
        return db_complaint
    except Exception as e:
        logger.error(f"Error submitting complaint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit complaint: {str(e)}")

@router.get("", response_model=PaginatedComplaints)
async def get_complaints_list(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query in text, summary, topic, or location"),
    topic_id: Optional[int] = Query(None, description="Filter by topic ID"),
    location: Optional[str] = Query(None, description="Filter by branch location/city"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (POSITIVE, NEGATIVE, NEUTRAL)"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    source: Optional[str] = Query(None, description="Filter by channel source"),
    user_type: Optional[str] = Query(None, description="Filter by customer tier"),
    intensity_min: Optional[float] = Query(None, description="Minimum intensity rating (0.0 to 1.0)"),
    intensity_max: Optional[float] = Query(None, description="Maximum intensity rating (0.0 to 1.0)"),
    date_start: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    date_end: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    """Fetches a paginated, filtered list of complaints."""
    total, items = await complaint_service.get_complaints(
        db, page=page, limit=limit, search=search, topic_id=topic_id,
        location=location, sentiment=sentiment, severity=severity,
        source=source, user_type=user_type, intensity_min=intensity_min,
        intensity_max=intensity_max, date_start=date_start, date_end=date_end
    )
    
    pages = (total + limit - 1) // limit if total > 0 else 0
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "items": items
    }

@router.get("/export/csv")
async def export_complaints(
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
    """Generates and downloads a CSV export file of filtered complaints."""
    csv_content = await complaint_service.export_complaints_csv(
        db, search=search, topic_id=topic_id, location=location,
        sentiment=sentiment, severity=severity, source=source,
        user_type=user_type, intensity_min=intensity_min, intensity_max=intensity_max,
        date_start=date_start, date_end=date_end
    )
    
    return FastAPIResponse(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=complaint_intelligence_export.csv"
        }
    )

@router.post("/retrain", status_code=200)
async def trigger_topic_retraining(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers topic re-clustering (BERTopic / fallback KMeans) on all database complaints.
    Runs asynchronously and alerts dashboards to refresh via WebSocket when complete.
    """
    async def retrain_task():
        try:
            num_topics = await complaint_service.retrain_all_topics(db)
            await manager.broadcast({"event": "topics_updated", "data": {"total_topics": num_topics}})
        except Exception as e:
            logger.error(f"Async topic retraining failed: {e}", exc_info=True)
            
    background_tasks.add_task(retrain_task)
    return {"status": "retraining_scheduled", "message": "Topic modeling retraining started in background."}

@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint_details(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetches details of a specific complaint by UUID."""
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint
