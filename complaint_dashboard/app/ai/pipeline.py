import datetime
import json
import re
import logging
from typing import Dict, Any, List, Optional

from app.ai.sentiment import analyze_sentiment, calculate_intensity
from app.ai.topic_model import get_embedding, match_closest_topic
from app.ai.llm import generate_complaint_analysis

logger = logging.getLogger(__name__)

def preprocess_text(text: str) -> str:
    """Preprocesses customer complaints by cleaning white spaces and removing noise."""
    if not text:
        return ""
    # Remove HTML tags if any
    cleaned = re.sub(r'<[^>]*>', '', text)
    # Standardize white space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Strip leading/trailing spaces
    return cleaned.strip()

def classify_severity(
    intensity_score: float, 
    user_type: str, 
    complaint_source: str, 
    text: str
) -> str:
    """
    Classifies severity dynamically: low, medium, high, critical.
    Depends on:
    - Sentiment intensity
    - Complaint source (e.g. social media threats are higher PR risk)
    - User type (premium/business tiers get prioritized SLAs)
    - Critical keywords (e.g. fraud, legal action, unauthorized)
    """
    text_lower = text.lower()
    
    # 1. Critical triggers (fraud, unauthorized transaction, security hacks, legal threat)
    critical_triggers = ["fraud", "unauthorized", "unauthorised", "stolen", "hacked", "scam", "cyber", "police", "legal", "court", "lawyer"]
    has_critical_trigger = any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in critical_triggers)
    
    # 2. Assign base severity class based on intensity
    if intensity_score >= 0.80:
        base_severity = "critical"
    elif intensity_score >= 0.55:
        base_severity = "high"
    elif intensity_score >= 0.30:
        base_severity = "medium"
    else:
        base_severity = "low"
        
    # 3. Elevate based on customer tier and channel PR risk
    # Premium or Business clients with negative/neutral indicators get prioritized
    if user_type.lower() in ["premium", "business"] and base_severity == "medium":
        base_severity = "high"
        
    # Social media complaints have high visibility and PR impact
    if complaint_source.lower() == "social media" and base_severity == "medium":
        base_severity = "high"
    elif complaint_source.lower() == "social media" and base_severity == "high":
        base_severity = "critical"
        
    # Cyber security or financial theft overrides directly to critical
    if has_critical_trigger and intensity_score >= 0.40:
        return "critical"
        
    return base_severity

async def run_ai_pipeline(
    complaint_text: str,
    user_type: str,
    complaint_source: str,
    location: Optional[str] = "Unknown",
    complaint_date: Optional[str] = None,
    complaint_time: Optional[str] = None,
    existing_topic_centroids: Optional[Dict[int, List[float]]] = None
) -> Dict[str, Any]:
    """
    Runs the entire AI pipeline:
    1. Preprocesses text
    2. Runs sentiment analysis
    3. Calculates intensity
    4. Evaluates severity
    5. Computes text embedding and assigns closest topic centroid
    6. Generates LLM analysis (summary, root cause, solving steps, department, escalation priority)
    7. Formats data for DB insertion
    """
    logger.info("Starting AI pipeline execution...")
    
    # Preprocess
    cleaned_text = preprocess_text(complaint_text)
    
    # Sentiment
    sentiment_result = analyze_sentiment(cleaned_text)
    sentiment_label = sentiment_result["label"]
    sentiment_score = sentiment_result["score"]
    
    # Intensity
    intensity_score = calculate_intensity(cleaned_text, sentiment_label, sentiment_score)
    
    # Severity
    severity = classify_severity(intensity_score, user_type, complaint_source, cleaned_text)
    
    # Embeddings and Topic matching
    embedding = get_embedding(cleaned_text)
    embedding_json = json.dumps(embedding)
    
    topic_id = -1
    topic_label = "Uncategorized"
    topic_keywords_json = json.dumps([])
    
    if existing_topic_centroids:
        # Match against database topic centroids
        topic_id = match_closest_topic(embedding, existing_topic_centroids)
        # We'll set the label later during database mapping or return topic_id for service layer lookup
    
    # LLM generation (summary, cause, steps, routing department, priority)
    llm_analysis = await generate_complaint_analysis(cleaned_text)
    
    # Handle optional date and time
    now = datetime.datetime.utcnow()
    final_date = complaint_date or now.strftime("%Y-%m-%d")
    final_time = complaint_time or now.strftime("%H:%M:%S")
    
    try:
        dt_obj = datetime.datetime.strptime(f"{final_date} {final_time}", "%Y-%m-%d %H:%M:%S")
    except Exception:
        dt_obj = now
        
    return {
        "complaint_text": complaint_text,
        "cleaned_text": cleaned_text,
        "complaint_date": final_date,
        "complaint_time": final_time,
        "timestamp": dt_obj,
        "location": location or "Unknown",
        "user_type": user_type,
        "complaint_source": complaint_source,
        "embedding_vector_reference": embedding_json,
        "topic_id": topic_id,
        "topic_label": topic_label, # Will be set/overridden by service
        "topic_keywords": topic_keywords_json,
        "sentiment_label": sentiment_label,
        "sentiment_score": sentiment_score,
        "intensity_score": intensity_score,
        "severity": severity,
        "ai_summary": llm_analysis.get("summary", ""),
        "root_cause": llm_analysis.get("root_cause", ""),
        "solving_steps": json.dumps(llm_analysis.get("solving_steps", [])),
        "recommended_department": llm_analysis.get("recommended_department", "Customer Support"),
        "escalation_priority": llm_analysis.get("escalation_priority", "low")
    }
