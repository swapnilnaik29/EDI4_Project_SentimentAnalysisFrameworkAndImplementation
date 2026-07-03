from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sys

# Adjust path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_dashboard_stats, get_filtered_reviews, update_review_nlp_data, get_connection
from nlp_engine import nlp_engine
from llm_engine import llm_engine

app = FastAPI(title="Advanced SentiWise Analysis Pipeline API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")


@app.on_event("startup")
async def startup_event():
    # Initialize SQLite and load data if available
    init_db()

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/process_batch")
def process_batch(background_tasks: BackgroundTasks):
    """Triggers background NLP processing for reviews missing AI data."""
    def process_reviews():
        # Load heavy models only when batch processing starts
        nlp_engine.load_models()
        
        conn = get_connection()
        # Find reviews that haven't been processed
        unprocessed = conn.execute("SELECT review_id, review_text FROM reviews WHERE ai_sentiment IS NULL LIMIT 100").fetchall()
        
        if not unprocessed:
            conn.close()
            return
            
        review_ids = [row[0] for row in unprocessed]
        texts = [row[1] for row in unprocessed]
        
        results = nlp_engine.analyze_batch(texts)
        
        for r_id, result in zip(review_ids, results):
            update_review_nlp_data(
                r_id,
                result['sentiment'],
                result['emotion'],
                result['intent'],
                result['toxicity'],
                result['topic'],
                result['entities']
            )
        conn.close()

    background_tasks.add_task(process_reviews)
    return {"message": "Batch processing started in the background."}

@app.get("/api/dashboard/stats")
def dashboard_stats():
    """Returns aggregated stats for the dashboard."""
    try:
        stats = get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reviews")
def get_reviews(limit: int = None, offset: int = 0, sentiment: str = None, bu: str = None):
    """Returns a list of reviews with optional filtering."""
    reviews = get_filtered_reviews(limit, offset, sentiment, bu)
    return {"data": reviews}

import json

class SummaryRequest(BaseModel):
    bu: str = None
    force_refresh: bool = False

@app.post("/api/insights/summary")
def get_summary(request: SummaryRequest):
    """Generates an executive summary using Ollama Mistral and caches it."""
    result_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "result")
    os.makedirs(result_dir, exist_ok=True)
    
    cache_file = os.path.join(result_dir, f"summary_cache_{request.bu or 'all'}.json")
    
    if not request.force_refresh and os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)

    conn = get_connection()
    query = "SELECT review_text FROM reviews"
    if request.bu:
        query += f" WHERE business_unit = '{request.bu}'"
    query += " LIMIT 20"
    
    reviews = [row[0] for row in conn.execute(query).fetchall()]
    conn.close()
    
    if not reviews:
        return {"summary": "No reviews found for the specified criteria."}
        
    summary = llm_engine.generate_summary(reviews)
    
    result = {"summary": summary}
    with open(cache_file, "w") as f:
        json.dump(result, f)
        
    return result
