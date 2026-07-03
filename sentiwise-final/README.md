# Sentiment Analysis & Topic Insight Framework

A modular Python framework for **topic-wise sentiment analysis and summarization of user-generated textual data** such as reviews and comments.

The framework processes datasets stored in **tabular formats (CSV)** and applies Natural Language Processing (NLP) techniques to extract structured insights including:

- Sentiment classification
- Topic extraction
- Topic-wise sentiment analysis
- Topic-wise summaries
- Data visualization
- Exportable analytical results

The project demonstrates how a **unified analytical pipeline** can transform raw textual data into interpretable insights.

---

## Table of Contents
- [Motivation](#motivation)
- [Features](#features)
- [Framework Architecture](#framework-architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Example Usage](#example-usage)
- [Notebook Demonstration](#notebook-demonstration)
- [Example Output](#example-output)
- [Technologies Used](#technologies-used)
- [Future Improvements](#future-improvements)
- [Author](#author)

---

## Motivation

User-generated reviews contain valuable insights about products, services, and experiences. However, analyzing thousands of reviews manually is impractical.

This framework automates the process by:

- Identifying **key discussion topics**
- Determining **sentiment trends**
- Generating **concise summaries**
- Providing **structured analytical outputs**

The framework is designed to be **reusable, modular, and extensible** for different domains.

---

## Features

### 1. Automatic Text Preprocessing
Cleans and normalizes textual input through:
- Lowercasing
- URL removal
- Punctuation cleanup
- Whitespace normalization

### 2. Sentiment Analysis
Classifies each review into:
- **Positive**
- **Neutral**
- **Negative**

**Example Output:**

| Review | Sentiment |
|--------|-----------|
| Great product and fast delivery | Positive |
| The battery drains quickly | Negative |

### 3. Topic Extraction
Automatically discovers the **main topics discussed in reviews** using embeddings and clustering.

**Example Discovered Topics:**
```
Topic 1: delivery
Topic 2: battery
Topic 3: customer_support
```

Topics are stored in dataframe columns:
```
topic1 | topic2 | topic3
```

### 4. Topic-wise Sentiment Analysis
Analyzes sentiment distribution for each topic to identify **which aspects users like or dislike**.

**Example Matrix:**

| Topic | Positive | Neutral | Negative |
|-------|----------|---------|----------|
| delivery | 12 | 2 | 6 |
| battery | 7 | 1 | 8 |
| support | 15 | 0 | 2 |

### 5. Summarization

**Individual Reviews:**
```python
data.summarise(row=5)
```
*Output: "The user reports delayed delivery but satisfactory product quality."*

**Entire Dataset:**
```python
data = data.summarise()
```
Adds a `summary` column to the dataframe.

### 6. Topic-wise Summaries
Reviews belonging to the same topic are merged and summarized.

**Example:**
```
Topic: delivery
Summary: Many users complain about delayed shipping and damaged packaging.

Topic: battery
Summary: Several reviews mention poor battery life and overheating.
```

### 7. Visualization
Basic analytical visualizations including:
- Sentiment distribution
- Topic sentiment matrices

**Example:**
```python
data.visualise("bar", "sentiment")
```

### 8. Export Results
Processed results can be exported as a CSV file.

```python
data.export("results/result.csv")
```

The exported dataset includes:
- `sentiment`
- `topics`
- `summaries`

---

## Framework Architecture

```
Dataset (CSV)
      ↓
LoadDataFrame
      ↓
Text Preprocessing
      ↓
Sentence Embeddings
      ↓
Topic Extraction
      ↓
Sentiment Analysis
      ↓
Topic-wise Sentiment
      ↓
Summarization
      ↓
Visualization + Export
```

---

## Project Structure

```
sentiwise/
│
├── src/
│   └── sentiwise/
│       ├── core/
│       │   └── senti_data.py
│       ├── preprocessing/
│       ├── sentiment/
│       ├── topics/
│       ├── summarization/
│       ├── models/
│       └── utils/
│
├── notebooks/
│   └── demo.ipynb
│
├── data/
│   └── reviews_dataset_large.csv
│
├── results/
│
├── examples/
│   └── demo.py
│
├── requirements.txt
└── README.md
```

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/sentiwise.git
   ```

2. **Enter the project directory:**
   ```bash
   cd sentiwise
   ```

3. **Create a virtual environment:**
   ```bash
   python -m venv env
   ```

4. **Activate the environment:**

   *Windows:*
   ```bash
   env\Scripts\activate
   ```

   *macOS/Linux:*
   ```bash
   source env/bin/activate
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Install Ollama (Optional, for summarization):**
   Download and run Ollama from https://ollama.com and run your local model (e.g., `ollama run mistral`).

---

## Example Usage

SentiWise uses a developer-friendly fluent API that allows for easy method chaining without exposing internal data structures like Pandas DataFrames.

```python
from sentiwise.core.senti_data import SentiData

# 1. Load Data
data = SentiData(file_path="data/reviews_dataset_large.csv")

# 2. Run the Advanced Pipeline
data.analyze_sentiment() \
    .detect_toxicity() \
    .extract_ner() \
    .extract_advanced(model="mistral")

# 3. Time-Series Plot
ts_data = data.time_series(freq="W")
from sentiwise.visualization.plotter import plot_time_series
plot_time_series(ts_data)
```

---

## Notebook Demonstration

A complete demonstration notebook is available at:
```
notebooks/demo.ipynb
```

This notebook walks through the full analytical pipeline with step-by-step explanations.

---

## Example Output

**Sentiment Distribution:**
```
positive    0.55
neutral     0.21
negative    0.24
```

**Extracted Topics:**
```
delivery
battery
support
```

**Topic-wise Summary:**
```
delivery → many users report delays in shipping
battery → several reviews discuss battery performance issues
support → customer support experiences are mostly positive
```

---

## Features

- **Advanced NLP Pipeline**: Powered by HuggingFace Transformers and Ollama.
- **Aspect-Based Sentiment Analysis (ABSA)**: Identifies specific product features and their sentiments.
- **Intent Detection**: Classifies the review's goal (complaint, feature request, churn risk).
- **Emotion & Subjectivity**: Extracts the primary emotion (joy, sadness, anger) from text.
- **Sarcasm & Toxicity Detection**: Flags sarcastic or toxic/abusive content.
- **Named Entity Recognition (NER)**: Extracts companies, products, and locations mentioned.
- **Time-Series Tracking**: Plots and tracks sentiment trends over time.
- **Per-Review Topic Extraction**: Extracts the single most relevant topic per review.
- **Chainable API**: Easy to use, fluent API abstracting away Pandas and model complexities.

---

## Technologies Used

- **Python** - Core programming language
- **Pandas** - Data manipulation and analysis
- **HuggingFace Transformers** - Pre-trained NLP models
- **Sentence Transformers** - Sentence embeddings
- **Scikit-learn** - Clustering and machine learning
- **PyTorch** - Deep learning framework
- **Matplotlib** - Data visualization
- **Seaborn** - Statistical data visualization

---

## Future Improvements

Planned enhancements include:

- [ ] Multi-word topic labeling
- [ ] Improved topic modeling with BERTopic
- [ ] Interactive dashboards
- [ ] Multilingual support
- [ ] Real-time streaming analysis
- [ ] API endpoint creation
- [ ] Custom model fine-tuning capabilities

---


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

---

## Show Your Support

Give a ⭐️ if this project helped you!
