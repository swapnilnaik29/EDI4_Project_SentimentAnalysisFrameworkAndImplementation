import csv
import io
import json
import uuid
import datetime
import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Complaint
from app.schemas.complaint import ComplaintCreate
from app.ai.pipeline import run_ai_pipeline
from app.ai.topic_model import cluster_complaints

logger = logging.getLogger(__name__)

async def get_topic_centroids(db: AsyncSession) -> Dict[int, List[float]]:
    """Calculates the average embedding vector for each topic cluster in the database."""
    try:
        # Fetch topic_id and embeddings for all complaints
        result = await db.execute(
            select(Complaint.topic_id, Complaint.embedding_vector_reference)
            .where(Complaint.topic_id != -1)
        )
        rows = result.all()
        
        if not rows:
            return {}
            
        # Group embeddings by topic_id
        topic_embeddings = {}
        for r in rows:
            t_id, emb_str = r[0], r[1]
            if not emb_str:
                continue
            try:
                emb = json.loads(emb_str)
                if t_id not in topic_embeddings:
                    topic_embeddings[t_id] = []
                topic_embeddings[t_id].append(emb)
            except Exception:
                continue
                
        # Calculate mean vector per topic
        centroids = {}
        for t_id, embs in topic_embeddings.items():
            arr = np.array(embs)
            centroid = np.mean(arr, axis=0)
            centroids[t_id] = centroid.tolist()
            
        return centroids
    except Exception as e:
        logger.error(f"Error computing centroids: {e}")
        return {}

async def get_topic_metadata(db: AsyncSession, topic_id: int) -> Tuple[str, List[str]]:
    """Retrieves the label and keywords of an existing topic from the database."""
    try:
        result = await db.execute(
            select(Complaint.topic_label, Complaint.topic_keywords)
            .where(Complaint.topic_id == topic_id)
            .limit(1)
        )
        row = result.first()
        if row:
            label, kw_str = row[0], row[1]
            keywords = json.loads(kw_str) if kw_str else []
            return label, keywords
    except Exception as e:
        logger.error(f"Error fetching topic metadata: {e}")
    return "Uncategorized", []

async def create_complaint(db: AsyncSession, schema: ComplaintCreate) -> Complaint:
    """Runs the AI pipeline, maps to topics, and stores the complaint in the database."""
    complaint_id = str(uuid.uuid4())
    
    # 1. Fetch existing centroids to categorize incoming complaint
    centroids = await get_topic_centroids(db)
    
    # 2. Run AI extraction
    ai_data = await run_ai_pipeline(
        complaint_text=schema.complaint_text,
        user_type=schema.user_type,
        complaint_source=schema.complaint_source,
        location=schema.location,
        complaint_date=schema.complaint_date,
        complaint_time=schema.complaint_time,
        existing_topic_centroids=centroids
    )
    
    # 3. Apply topic details if matched
    topic_id = ai_data["topic_id"]
    if topic_id != -1:
        label, keywords = await get_topic_metadata(db, topic_id)
        ai_data["topic_label"] = label
        ai_data["topic_keywords"] = json.dumps(keywords)
    else:
        ai_data["topic_label"] = "Uncategorized"
        ai_data["topic_keywords"] = json.dumps([])
        
    # 4. Instantiate and save model
    db_complaint = Complaint(
        complaint_id=complaint_id,
        **ai_data
    )
    
    db.add(db_complaint)
    await db.flush()
    return db_complaint

async def get_complaints(
    db: AsyncSession,
    page: int = 1,
    limit: int = 10,
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
) -> Tuple[int, List[Complaint]]:
    """Fetches complaints matching filters with pagination."""
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
        
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0
    
    # Apply ordering and limit
    query = query.order_by(Complaint.timestamp.desc())
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    complaints = result.scalars().all()
    
    return total_count, list(complaints)

async def get_complaint_by_id(db: AsyncSession, complaint_id: str) -> Optional[Complaint]:
    """Retrieves a single complaint details by ID."""
    result = await db.execute(select(Complaint).where(Complaint.complaint_id == complaint_id))
    return result.scalar_one_or_none()

async def export_complaints_csv(
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
) -> str:
    """Exports filtered complaints list to CSV formatted string."""
    # Run query without pagination limit
    _, complaints = await get_complaints(
        db, page=1, limit=100000, search=search, topic_id=topic_id,
        location=location, sentiment=sentiment, severity=severity,
        source=source, user_type=user_type, intensity_min=intensity_min,
        intensity_max=intensity_max, date_start=date_start, date_end=date_end
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Complaint ID", "Original Text", "Cleaned Text", "Date", "Time", "Timestamp",
        "Location", "Customer Tier", "Channel Source", "Topic ID", "Topic Title",
        "Sentiment", "Sentiment Score", "Intensity Score", "Severity Grade",
        "AI Summary", "Root Cause", "Solving Steps", "Recommended Dept", "Escalation Priority"
    ])
    
    for c in complaints:
        # Load solving steps from JSON
        steps = []
        if c.solving_steps:
            try:
                steps = json.loads(c.solving_steps)
            except Exception:
                steps = [c.solving_steps]
        steps_str = "; ".join(steps)
        
        writer.writerow([
            c.complaint_id, c.complaint_text, c.cleaned_text, c.complaint_date, c.complaint_time, 
            c.timestamp.isoformat() if c.timestamp else "", c.location, c.user_type, c.complaint_source,
            c.topic_id, c.topic_label, c.sentiment_label, c.sentiment_score, c.intensity_score,
            c.severity, c.ai_summary, c.root_cause, steps_str, c.recommended_department, c.escalation_priority
        ])
        
    return output.getvalue()

async def retrain_all_topics(db: AsyncSession) -> int:
    """Loads all complaints from DB, fits topic clustering, and updates DB mappings."""
    logger.info("Initializing dynamic topic retraining...")
    
    # 1. Fetch all complaints
    result = await db.execute(select(Complaint))
    complaints = result.scalars().all()
    
    if not complaints:
        logger.info("No complaints found in DB to cluster.")
        return 0
        
    complaint_dicts = []
    for c in complaints:
        complaint_dicts.append({
            "complaint_id": c.complaint_id,
            "complaint_text": c.complaint_text,
            "cleaned_text": c.cleaned_text
        })
        
    # 2. Run clustering
    topic_ids, topic_info = await cluster_complaints(complaint_dicts)
    
    # 3. Update records in the database
    updated_count = 0
    for idx, c in enumerate(complaints):
        t_id = topic_ids[idx]
        t_meta = topic_info.get(t_id, {"label": "Uncategorized", "keywords": []})
        
        c.topic_id = t_id
        c.topic_label = t_meta["label"]
        c.topic_keywords = json.dumps(t_meta["keywords"])
        
        updated_count += 1
        
    await db.commit()
    logger.info(f"Retrained topics. Updated {updated_count} complaints with {len(topic_info)} unique topics.")
    return len(topic_info)
