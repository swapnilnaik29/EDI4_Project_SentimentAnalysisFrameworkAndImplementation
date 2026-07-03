# SentiWise Framework Documentation

Welcome to the comprehensive documentation for the **SentiWise** framework. This document covers everything from project setup to deep technical architectures, the features implemented, and syntax guidelines for effectively using the framework.

---

## 1. Project Overview & Philosophy

SentiWise is an advanced, modular Python framework designed for the automated processing, analysis, and visualization of textual data (specifically user reviews, feedback, or social media comments). 

### The Core Design Paradigm
SentiWise abstracts away complex data manipulation (Pandas) and Machine Learning pipelines (HuggingFace, Scikit-Learn, Ollama) by encapsulating logic within a fluent API class: `SentiData`. 

Users interact with the framework by chaining highly expressive, readable methods. When data is extracted or visualized, it is returned as standard Python lists or dictionaries, completely decoupling the end user from Pandas dependency overhead.

---

## 2. Setup & Installation

### Prerequisites
1. **Python 3.8+** (3.10+ recommended)
2. **Ollama** (Required for Advanced Extraction and Summarization)
   - Download from [ollama.com](https://ollama.com/)
   - Pull the model: `ollama run mistral`

### Installation Steps
1. **Clone the Repository & Navigate to Directory**:
   ```bash
   git clone <repository_url>
   cd sentiment_analyzer
   ```

2. **Setup Virtual Environment**:
   ```bash
   # Windows
   python -m venv env
   env\Scripts\activate

   # Mac/Linux
   python3 -m venv env
   source env/bin/activate
   ```

3. **Install Dependencies**:
   Install the module globally in editable mode:
   ```bash
   pip install -e .
   ```

---

## 3. Core Architecture & Technologies

| Layer | Technology | Purpose |
|---|---|---|
| **Core Structure** | Python 3.10, Pandas | Backend data parsing, schema validation, and storage. |
| **Sentiment & NER** | HuggingFace Pipelines | Pre-trained RoBERTa models (`cardiffnlp/twitter-roberta-base-sentiment`), Toxicity models, and BERT NER (`dslim/bert-base-NER`). |
| **Topic Clustering** | SentenceTransformers, Scikit-Learn | Converts text to embeddings, clusters via KMeans, and extracts labels via TF-IDF. |
| **Super Extractor** | Ollama (Mistral) | Zero-shot generation to extract ABSA (Aspect-Based Sentiment), Intent, Emotion, and Sarcasm. |
| **Visualization** | Matplotlib / Seaborn | Hidden behind `SentiData.visualize()` for one-line graphing without boilerplate code. |

---

## 4. Feature Deep Dive & Syntax Guide

Below are the primary capabilities of the `SentiData` object.

### A. Data Initialization
The framework expects a CSV containing at minimum a `content` column and a `timestamp` column. The schema is automatically validated and cleaned.

```python
from sentiwise.core.senti_data import SentiData
data = SentiData("data/sample_reviews.csv")
```

### B. The Fluent Pipeline
You can chain analytical methods together. Each method modifies the internal DataFrame and returns the `SentiData` instance.

```python
data.analyze_sentiment() \
    .detect_toxicity() \
    .extract_ner() \
    .extract_advanced(model="mistral") \
    .extract_topics(size=5)
```

### C. Details of Individual Methods

#### 1. Sentiment Analysis
- **Method:** `analyze_sentiment()`
- **Mechanics:** Feeds text through `cardiffnlp/twitter-roberta-base-sentiment`. Returns Positive, Neutral, or Negative labels.

#### 2. Super Extraction (Advanced Features)
- **Method:** `extract_advanced(model="mistral")`
- **Mechanics:** Pings a local Ollama server to extract high-level conversational attributes:
  - **ABSA:** Aspect-Based Sentiment Analysis (e.g., "The battery is terrible but screen is great").
  - **Intent:** Classifies if review is a 'complaint', 'feature request', or 'praise'.
  - **Emotion:** Categorizes tone (Joy, Anger, Sadness, etc.).
  - **Sarcasm:** Boolean flag detecting sarcastic phrasing.

#### 3. Toxicity Detection
- **Method:** `detect_toxicity()`
- **Mechanics:** Uses `martin-ha/toxic-comment-model` to flag abusive or hate-speech comments.

#### 4. Named Entity Recognition (NER)
- **Method:** `extract_ner()`
- **Mechanics:** Uses BERT to locate and classify companies, locations, or products within the text.

#### 5. Topic Modeling
- **Method:** `extract_topics(size=3)`
- **Mechanics:** Converts all reviews to vector embeddings, runs a KMeans clustering algorithm, and names the topics using TF-IDF bigrams.
- **Related Summaries:**
  - `topic_sentiment()`: Returns a matrix cross-referencing topics with sentiment.
  - `topic_summary(model="mistral")`: Uses Ollama to generate a paragraph summary for each cluster.

### D. Time-Series Tracking
You can track sentiment fluctuations over time (Days `D`, Weeks `W`, or Months `M`).

```python
time_data = data.time_series(freq="W")
print(time_data)
```

### E. Data Viewing & Exporting

**Viewing Data:**
Returns data abstracted away from Pandas as pure Python lists of dicts.
```python
# View top 5 rows
print(data.head(5))

# Filter by column
negative_reviews = data.filter_by("sentiment", "negative")
```

**Exporting Results:**
Easily save your fully enriched dataset back to a CSV for external use (BI tools, Excel).
```python
data.export("results/my_processed_data.csv")
```

---

## 5. Visualizing Data

You do not need to import Matplotlib manually. Just call `visualize`.

```python
# Plot a bar chart of sentiments
data.visualize("bar", "sentiment")

# Plot a bar chart of intents
data.visualize("bar", "intent")
```

---

*This framework prioritizes clean syntax and rapid extraction. For more examples, see the `examples/` directory or run `notebooks/sample.ipynb`.*
