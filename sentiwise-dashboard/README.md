# Advanced SentiWise Analysis Pipeline

A fully local, production-style AI-powered sentiment intelligence web application.

## Prerequisites

1. **Python 3.10+**
2. **Ollama**: Must be installed locally (from [ollama.com](https://ollama.com/)).
3. **Mistral Model**: Run `ollama run mistral` in your terminal to download and start the model before running the application.

## Installation

1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

## Running the Application

Double-click the `run.bat` script, or run it from your terminal:

```bash
run.bat
```

This script will automatically:
1. Generate the synthetic review dataset if it doesn't exist.
2. Start the FastAPI backend and serve the frontend dashboard.

Once running, navigate to:
**http://127.0.0.1:8000/app/index.html**

## Features

- **Local NLP Pipeline**: Uses HuggingFace models for Sentiment, Emotion, and Toxicity. NER via spaCy.
- **Local LLM Insights**: Connects to Ollama (Mistral) to generate executive summaries and extract root causes from reviews.
- **Modern Dashboard**: Built with Vanilla JS, Tailwind CSS, ECharts, and Plotly.
- **Interactive Review Explorer**: Search, filter, and drill down into individual reviews.
- **Data Privacy**: Everything runs 100% locally. No data is sent to the cloud.
