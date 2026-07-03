# Bank Complaint Intelligence System (BCIS)

An offline, local, AI-powered banking complaints intelligence and analytics platform. BCIS processes incoming complaints through a series of natural language pipelines, generates semantic embeddings, groups records dynamically into discovered categories using clustering, evaluates sentiment and urgency, and routes alerts in real-time to a modern dashboard.

---

## Key Highlights

- **Real-Time Streaming**: Live streaming of processed complaints directly to admin client dashboards using FastAPI WebSockets.
- **Dynamic Topic Modeling**: Employs SentenceTransformers (`all-MiniLM-L6-v2`) and BERTopic (with scikit-learn fallback) to group complaints without pre-defined hardcoded categories.
- **Urgency & Severity Evaluation**: Dynamic severity calculations utilizing customer tiers, social media PR risk multipliers, negative sentiment confidence, and capital letters shout ratios.
- **Completely Offline**: Powered by local HuggingFace transformers and a local Ollama instance running the `mistral` model.
- **High-Res Web Interfaces**: Glassmorphism submission portal and a dark/light responsive enterprise intelligence dashboard.
- **No-Break Failbacks**: Integrated fallbacks for sentiment, clustering, and LLM text generation so the system functions instantly without complex hardware.

---

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (Async/SQLite connection with `aiosqlite`), WebSockets, Uvicorn
- **AI / ML**: Sentence Transformers, BERTopic, UMAP, HDBSCAN, HuggingFace Transformers, Ollama (Mistral 7B)
- **Frontend**: Vanilla HTML5, CSS Variables, Vanilla JavaScript, Chart.js, Lucide Icons

---

## Local Setup Instructions

### 1. Install Ollama and Get Mistral
1. Download and install **Ollama** from [ollama.com](https://ollama.com/).
2. Start the Ollama application.
3. Open your terminal and pull the required Mistral model:
   ```bash
   ollama pull mistral
   ```

### 2. Python Environment Setup
1. Clone or navigate to the workspace directory:
   ```bash
   cd e:/College/SEM 4/EDI/complaint_dashboard
   ```
2. Create and activate a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install all required dependencies listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: On Windows, installing HDBSCAN might require Visual Studio C++ Build Tools. If it fails, the script will automatically fallback to standard scikit-learn KMeans clustering, so the application will still run perfectly!)*

### 3. Database Seeding (Sample Data)
To pre-populate your command center dashboard with 20+ realistic banking complaints spread across dates, locations, customer tiers, and channels:
```bash
python generate_sample_data.py
```
This script will initialize SQLite tables, insert sample documents, and run the dynamic clustering model to discover topics immediately.

---

## Run Instructions

Launch the FastAPI backend:
```bash
python run.py
```

### Accessing the Web Portals
Once the server starts up, open your browser and navigate to:
- **Complaint Submission Portal**: [http://localhost:8000/submit](http://localhost:8000/submit)
- **Staff Intelligence Dashboard**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)

---

## Modular System Directory Structure

```
complaint_dashboard/
│
├── app/
│   ├── main.py                     # FastAPI application router setup
│   │
│   ├── database/
│   │   ├── connection.py           # Async engine and SQLite DB setup
│   │   └── models.py               # SQLAlchemy Complaint model
│   │
│   ├── schemas/
│   │   └── complaint.py            # Pydantic validation structures
│   │
│   ├── ai/
│   │   ├── pipeline.py             # Ingestion coordination
│   │   ├── sentiment.py            # Sentiment analysis and intensity rating
│   │   ├── topic_model.py          # Embeddings and BERTopic clustering
│   │   └── llm.py                  # Ollama Mistral connection
│   │
│   ├── services/
│   │   ├── complaint_service.py    # Database operations and topic retraining
│   │   └── analytics_service.py    # Graph metrics aggregation
│   │
│   ├── routes/
│   │   ├── complaints.py           # REST endpoints for CRUD & CSV exports
│   │   ├── analytics.py            # REST endpoints for dashboard metrics
│   │   └── websockets.py           # WebSocket stream connection
│   │
│   ├── websocket/
│   │   └── manager.py              # Broadcast client manager
│   │
│   └── static/
│       ├── shared/css/             # Common design variables
│       ├── submit/                 # Portal web app
│       └── dashboard/              # Analytics dashboard web app
│
├── requirements.txt                # Python libraries
├── README.md                       # Documentation
├── run.py                          # Launcher script
└── generate_sample_data.py         # DB seeding script
```
