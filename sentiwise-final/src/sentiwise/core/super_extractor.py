import json
import requests
from tqdm import tqdm

def extract_advanced_features(texts, model="mistral"):
    """
    Uses Ollama to extract Topic, ABSA, Intent, Sarcasm, and Emotion in a single pass.
    """
    
    results = []
    
    print(f"\nRunning Super Extractor via Ollama ({model})... This may take a few minutes for large datasets.")
    
    for text in tqdm(texts):
        if not isinstance(text, str) or len(text.strip()) < 5:
            results.append({
                "topic": "unknown",
                "emotion": "neutral",
                "intent": "unknown",
                "sarcasm": False,
                "absa": []
            })
            continue

        prompt = f"""
Analyze the following review and extract the requested information.
Return ONLY valid JSON format, with no markdown formatting or extra text.

Review: "{text}"

JSON Schema:
{{
    "topic": "The single main keyword or short phrase describing the topic",
    "emotion": "One of: joy, sadness, anger, fear, surprise, disgust, neutral",
    "intent": "One of: praise, complaint, feature_request, churn_risk, support_request, factual",
    "sarcasm": true or false,
    "absa": [
        {{"aspect": "feature or component mentioned", "sentiment": "positive or negative"}}
    ]
}}
"""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json" # Force JSON mode if supported by the Ollama version
                },
                timeout=45
            )
            response.raise_for_status()
            
            result_json_str = response.json().get("response", "").strip()
            
            # Clean markdown if model still outputted it
            if result_json_str.startswith("```json"):
                result_json_str = result_json_str[7:-3].strip()
            elif result_json_str.startswith("```"):
                result_json_str = result_json_str[3:-3].strip()
                
            parsed = json.loads(result_json_str)
            
            # Ensure all keys exist
            results.append({
                "topic": parsed.get("topic", "unknown"),
                "emotion": parsed.get("emotion", "neutral"),
                "intent": parsed.get("intent", "unknown"),
                "sarcasm": parsed.get("sarcasm", False),
                "absa": parsed.get("absa", [])
            })
            
        except Exception as e:
            # Fallback for errors
            results.append({
                "topic": "error",
                "emotion": "neutral",
                "intent": "unknown",
                "sarcasm": False,
                "absa": []
            })
            
    return results
