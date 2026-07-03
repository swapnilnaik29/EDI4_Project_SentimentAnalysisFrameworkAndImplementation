from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy
import os

class NLPEngine:
    def __init__(self):
        self.sentiment_analyzer = None
        self.ner_model = None
        self.models_loaded = False

    def load_models(self):
        if self.models_loaded:
            return
            
        print("Loading lightweight NLP Models...")
        try:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
            
            # NER
            print("Loading NER Model (spaCy)...")
            try:
                self.ner_model = spacy.load("en_core_web_sm") # using sm for speed
            except OSError:
                import subprocess
                print("Downloading spacy model...")
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
                self.ner_model = spacy.load("en_core_web_sm")
            
            self.models_loaded = True
            print("All NLP Models Loaded Successfully.")
        except Exception as e:
            print(f"Error loading models: {e}")

    def analyze_text(self, text):
        if not self.models_loaded:
            self.load_models()
            
        # 1. Sentiment (VADER)
        try:
            scores = self.sentiment_analyzer.polarity_scores(text)
            compound = scores['compound']
            if compound >= 0.05:
                sentiment_label = "Positive"
            elif compound <= -0.05:
                sentiment_label = "Negative"
            else:
                sentiment_label = "Neutral"
        except:
            sentiment_label = "Neutral"

        # 2. Emotion (Heuristics for extreme speed)
        emotion_label = "neutral"
        text_lower = text.lower()
        if sentiment_label == "Negative":
            if any(word in text_lower for word in ["angry", "mad", "furious", "hate", "terrible", "worst", "awful", "disgusting"]):
                emotion_label = "anger"
            elif any(word in text_lower for word in ["sad", "depressed", "disappointed", "upset", "sorry"]):
                emotion_label = "sadness"
            elif any(word in text_lower for word in ["fear", "scared", "afraid", "worried", "anxious"]):
                emotion_label = "fear"
            else:
                emotion_label = "disappointment"
        elif sentiment_label == "Positive":
            if any(word in text_lower for word in ["love", "amazing", "fantastic", "great", "excellent", "awesome", "perfect"]):
                emotion_label = "joy"
            elif any(word in text_lower for word in ["surprise", "wow", "unbelievable"]):
                emotion_label = "surprise"
            else:
                emotion_label = "happy"

        # 3. Toxicity (Heuristic for speed)
        toxicity_score = 0.0
        toxic_keywords = ["stupid", "idiot", "dumb", "hate", "suck", "terrible", "worst", "trash", "garbage", "bullshit", "fuck", "shit"]
        toxic_hits = sum(1 for word in toxic_keywords if word in text_lower)
        if toxic_hits > 0:
            toxicity_score = min(0.99, toxic_hits * 0.3)

        # 4. NER
        entities = []
        try:
            doc = self.ner_model(text)
            entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
        except:
            pass

        # 5. Intent
        intent = "feedback"
        if "?" in text or "how to" in text_lower or "help" in text_lower:
            intent = "question"
        elif "cancel" in text_lower or "refund" in text_lower or "return" in text_lower:
            intent = "complaint/churn"

        return {
            "sentiment": sentiment_label,
            "emotion": emotion_label,
            "toxicity": toxicity_score,
            "intent": intent,
            "entities": str(entities),
            "topic": "General" 
        }

    def analyze_batch(self, texts):
        if not self.models_loaded:
            self.load_models()
        return [self.analyze_text(t) for t in texts]

nlp_engine = NLPEngine()
