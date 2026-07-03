import re
import logging

logger = logging.getLogger(__name__)

# Try importing transformers. If it fails or fails to load, we fall back to a rule-based analyzer.
_sentiment_pipeline = None
try:
    from transformers import pipeline
    # Use a small, standard model that downloads quickly and runs locally on CPU/GPU
    _sentiment_pipeline = pipeline(
        "sentiment-analysis", 
        model="distilbert-base-uncased-finetuned-sst-2-english",
        device=-1 # Default to CPU for local compatibility
    )
    logger.info("HuggingFace sentiment analysis pipeline loaded successfully.")
except Exception as e:
    logger.warning(f"Could not load HuggingFace sentiment pipeline ({e}). Using rule-based fallback analyzer.")

# Urgency and intensity keywords for banking complaints
URGENT_KEYWORDS = {
    "fraud": 0.25,
    "stolen": 0.25,
    "blocked": 0.20,
    "hacked": 0.30,
    "unauthorized": 0.25,
    "scam": 0.20,
    "stole": 0.25,
    "police": 0.30,
    "court": 0.25,
    "legal": 0.20,
    "urgent": 0.20,
    "immediately": 0.15,
    "now": 0.05,
    "error": 0.08,
    "fail": 0.10,
    "failed": 0.10,
    "deducted": 0.15,
    "missing": 0.15,
    "lost": 0.15,
    "wrong": 0.08,
    "cancel": 0.05,
    "double": 0.10,
    "charge": 0.05
}

def analyze_sentiment_fallback(text: str) -> dict:
    """lexicon-based fallback sentiment analyzer if HF transformers is unavailable."""
    text_lower = text.lower()
    
    # Simple word counts
    positive_words = {"good", "great", "excellent", "happy", "resolve", "solved", "thanks", "helpful", "please", "appreciate"}
    negative_words = {"bad", "worst", "fail", "failed", "error", "poor", "stolen", "unauthorized", "deducted", "charged", "terrible", "issue", "problem", "broken", "blocked", "slow", "delay", "missing"}
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    if neg_count > pos_count:
        label = "NEGATIVE"
        score = 0.5 + min(0.49, neg_count * 0.1)
    elif pos_count > neg_count:
        label = "POSITIVE"
        score = 0.5 + min(0.49, pos_count * 0.1)
    else:
        label = "NEUTRAL"
        score = 0.5
        
    return {"label": label, "score": score}

def analyze_sentiment(text: str) -> dict:
    """Performs sentiment analysis using HuggingFace or fallback."""
    if _sentiment_pipeline:
        try:
            result = _sentiment_pipeline(text)[0]
            label = result["label"]  # 'POSITIVE' or 'NEGATIVE'
            score = result["score"]
            return {"label": label, "score": float(score)}
        except Exception as e:
            logger.error(f"Error in HuggingFace sentiment pipeline: {e}. Falling back.")
            
    return analyze_sentiment_fallback(text)

def calculate_intensity(text: str, sentiment_label: str, sentiment_score: float) -> float:
    """
    Calculates complaint intensity score from 0.0 to 1.0 based on:
    - Sentiment classification (negative sentiment starts higher)
    - Exclamation marks
    - Capitalized words (representing shouting)
    - Urgency keywords
    """
    intensity = 0.0
    
    # 1. Base score from sentiment
    if sentiment_label == "NEGATIVE":
        # Higher confidence in negative sentiment increases baseline intensity
        intensity += 0.3 + (sentiment_score * 0.2)
    elif sentiment_label == "NEUTRAL":
        intensity += 0.2
    else:
        intensity += 0.1
        
    # 2. Exclamation marks (indicates frustration)
    exclamations = text.count("!")
    intensity += min(0.15, exclamations * 0.05)
    
    # 3. Capitalized words ratio (shouting)
    words = re.findall(r'\b[A-Za-z]+\b', text)
    if words:
        caps_words = [w for w in words if w.isupper() and len(w) > 1]
        caps_ratio = len(caps_words) / len(words)
        intensity += min(0.20, caps_ratio * 0.40)
        
    # 4. Urgency/fraud keywords
    text_lower = text.lower()
    keyword_boost = 0.0
    for keyword, weight in URGENT_KEYWORDS.items():
        # Match word boundaries to avoid partial matches
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            keyword_boost += weight
            
    intensity += min(0.40, keyword_boost)
    
    # Clip between 0.0 and 1.0
    return round(max(0.0, min(1.0, intensity)), 2)
