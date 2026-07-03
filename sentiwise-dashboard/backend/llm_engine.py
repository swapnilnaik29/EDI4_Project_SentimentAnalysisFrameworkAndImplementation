import ollama
import json

class LLMEngine:
    def __init__(self, model_name="mistral"):
        self.model_name = model_name

    def generate_summary(self, reviews_text_list):
        """Generates an executive summary based on a list of reviews."""
        prompt = f"""
        You are a business intelligence AI analyzing customer reviews.
        Please provide a concise executive summary of the following reviews. 
        Highlight the top recurring complaints, customer pain points, and any positive trends.
        
        Reviews:
        {json.dumps(reviews_text_list)}
        
        Summary:
        """
        try:
            response = ollama.generate(model=self.model_name, prompt=prompt)
            return response['response']
        except Exception as e:
            print(f"Ollama error: {e}")
            return "Unable to generate summary. Ensure Ollama is running and the mistral model is installed."

    def extract_root_cause(self, review_text):
        """Extracts the root cause of a complaint."""
        prompt = f"""
        Analyze the following customer review and state the single root cause of their issue or complaint in one short phrase.
        If it's a positive review, state the main feature they liked.
        
        Review: "{review_text}"
        
        Root Cause / Main Feature:
        """
        try:
            response = ollama.generate(model=self.model_name, prompt=prompt)
            return response['response'].strip()
        except Exception as e:
            return "Unknown"

llm_engine = LLMEngine()
