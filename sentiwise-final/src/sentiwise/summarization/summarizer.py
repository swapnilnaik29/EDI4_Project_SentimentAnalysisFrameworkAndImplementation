import requests
import json

def summarize_text(text, model="mistral"):

    if not isinstance(text, str):
        return ""

    if len(text.strip()) < 20:
        return text

    prompt = f"Summarize the following review in one sentence. Only return the summary, do not add conversational fillers:\n{text}\nSummary:"

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code != 200:
            error_msg = response.text
            print(f"Warning: Summarization failed via Ollama (Status: {response.status_code}, Response: {error_msg}). Returning truncated text.")
            return text[:120]
            
        response.raise_for_status()
        
        result = response.json()
        summary = result.get("response", "").strip()
        
        if summary == "":
            return text[:120]
            
        return summary

    except Exception as e:
        print(f"Warning: Summarization failed via Ollama ({e}). Returning truncated text.")
        return text[:120]
