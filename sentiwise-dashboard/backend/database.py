import sqlite3
import pandas as pd
import os

DB_PATH = "e:/College/SEM 4/EDI/sentiwise-dashboard/data/sentiwise.sqlite"
CSV_PATH = "e:/College/SEM 4/EDI/sentiwise-dashboard/data/reviews_dataset.csv"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    
    # Check if reviews table exists
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'")
    
    if not cursor.fetchone():
        if os.path.exists(CSV_PATH):
            print(f"Loading data from {CSV_PATH} into SQLite...")
            df = pd.read_csv(CSV_PATH)
            
            # Add columns for NLP outputs if they don't exist
            # Sentiment, Emotion, Intent, Toxicity, Topic, Entities
            for col in ['ai_sentiment', 'ai_emotion', 'ai_intent', 'ai_topic', 'ai_entities']:
                if col not in df.columns:
                    df[col] = None
            if 'ai_toxicity' not in df.columns:
                df['ai_toxicity'] = None
                
            df.to_sql('reviews', conn, if_exists='replace', index=False)
        else:
            print("CSV file not found. Please generate sample data first.")
            
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_dashboard_stats():
    conn = sqlite3.connect(DB_PATH)
    stats = {}
    
    # Total reviews
    stats["total_reviews"] = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    
    # Average rating
    stats["avg_rating"] = conn.execute("SELECT AVG(rating) FROM reviews").fetchone()[0]
    
    # Sentiment distribution
    sentiment_dist = conn.execute("SELECT sentiment_label, COUNT(*) FROM reviews GROUP BY sentiment_label").fetchall()
    stats["sentiment_distribution"] = {row[0]: row[1] for row in sentiment_dist}
    
    # Top products
    top_products = conn.execute("SELECT product_or_service, COUNT(*) as c FROM reviews GROUP BY product_or_service ORDER BY c DESC LIMIT 5").fetchall()
    stats["top_products"] = [{"product": row[0], "count": row[1]} for row in top_products]
    
    # Time series (reviews per month)
    # Date might be in different format or need substr in SQLite, but assume YYYY-MM-DD
    # SQLite uses substr(date, 1, 7) for YYYY-MM if it's stored as ISO string
    time_series = conn.execute("SELECT substr(date, 1, 7) as month, COUNT(*) FROM reviews GROUP BY month ORDER BY month").fetchall()
    stats["time_series"] = [{"month": row[0], "count": row[1]} for row in time_series]
    
    conn.close()
    return stats

def get_filtered_reviews(limit=None, offset=0, sentiment=None, bu=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM reviews WHERE 1=1"
    
    if sentiment:
        query += f" AND sentiment_label = '{sentiment}'"
    if bu:
        query += f" AND business_unit = '{bu}'"
        
    if limit is not None:
        query += f" LIMIT {limit} OFFSET {offset}"
    elif offset > 0:
        query += f" LIMIT -1 OFFSET {offset}"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient="records")

def update_review_nlp_data(review_id, sentiment, emotion, intent, toxicity, topic, entities):
    conn = get_connection()
    query = """
    UPDATE reviews 
    SET ai_sentiment = ?, 
        ai_emotion = ?, 
        ai_intent = ?, 
        ai_toxicity = ?, 
        ai_topic = ?, 
        ai_entities = ?
    WHERE review_id = ?
    """
    # Use parameterized query for safety and to avoid formatting issues
    conn.execute(query, (sentiment, emotion, intent, toxicity, topic, entities, review_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
