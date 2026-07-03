import pandas as pd

from sentiwise.utils.schema_validator import validate_schema
from sentiwise.preprocessing.cleaner import clean_dataframe
from sentiwise.sentiment.sentiment_model import predict_sentiment
from sentiwise.topics.topic_model import extract_topics
from sentiwise.summarization.summarizer import summarize_text
from sentiwise.visualization.plotter import plot_bar
from sentiwise.core.super_extractor import extract_advanced_features
from sentiwise.models.model_manager import ModelManager
from tqdm import tqdm

class SentiData:
    def __init__(self, file_path=None, dataframe=None):
        if dataframe is not None:
            self._df = dataframe
        elif file_path is not None:
            self._df = pd.read_csv(file_path)
            validate_schema(self._df)
            self._df["timestamp"] = pd.to_datetime(self._df["timestamp"])
            self._df = clean_dataframe(self._df)
        else:
            raise ValueError("Must provide file_path or dataframe")

    def analyze_sentiment(self):
        """Analyzes sentiment and adds it to the dataset, returning self for chaining."""
        texts = self._df["content"].tolist()
        self._df["sentiment"] = predict_sentiment(texts)
        return self

    def extract_topics(self, size=3):
        # Kept for backward compatibility
        texts = self._df["content"].tolist()
        clusters, topics = extract_topics(texts, size)
        self._df["review_topic"] = clusters
        topic_mapping = {i: topic for i, topic in enumerate(topics)}
        self._df["topic"] = self._df["review_topic"].map(topic_mapping)
        return self

    def extract_advanced(self, model="mistral"):
        """Extracts Topic, ABSA, Intent, Sarcasm, and Emotion using Ollama."""
        texts = self._df["content"].tolist()
        results = extract_advanced_features(texts, model=model)
        
        self._df["topic"] = [r["topic"] for r in results]
        self._df["emotion"] = [r["emotion"] for r in results]
        self._df["intent"] = [r["intent"] for r in results]
        self._df["sarcasm"] = [r["sarcasm"] for r in results]
        self._df["absa"] = [str(r["absa"]) for r in results]
        return self
        
    def detect_toxicity(self):
        """Flags toxic reviews using HuggingFace."""
        texts = self._df["content"].tolist()
        tox_model = ModelManager.get_toxicity_model()
        
        print("\nDetecting Toxicity...")
        labels = []
        for i in tqdm(range(0, len(texts), 32)):
            batch = texts[i:i+32]
            results = tox_model(batch)
            for r in results:
                # martin-ha/toxic-comment-model returns 'toxic' or 'non-toxic'
                labels.append(r["label"] == "toxic")
        self._df["is_toxic"] = labels
        return self
        
    def extract_ner(self):
        """Extracts named entities (Companies, Products, Locations)."""
        texts = self._df["content"].tolist()
        ner_model = ModelManager.get_ner_model()
        
        print("\nExtracting Named Entities...")
        all_entities = []
        for text in tqdm(texts):
            if not isinstance(text, str):
                all_entities.append([])
                continue
            ents = ner_model(text)
            # Filter and get unique entities
            names = list(set([e["word"] for e in ents if e["score"] > 0.8]))
            all_entities.append(names)
            
        self._df["named_entities"] = [str(e) for e in all_entities]
        return self
        
    def time_series(self, freq="D"):
        """Aggregates sentiment over time. freq: 'D' for day, 'W' for week, 'M' for month."""
        if "sentiment" not in self._df.columns:
            self.analyze_sentiment()
            
        # Map sentiment to numeric score
        mapping = {"positive": 1, "neutral": 0, "negative": -1}
        self._df["sentiment_score"] = self._df["sentiment"].map(mapping)
        
        ts_df = self._df.set_index("timestamp")
        grouped = ts_df.resample(freq)["sentiment_score"].mean().reset_index()
        
        return grouped.to_dict(orient="records")

    def summarize(self, row=None, model="mistral"):
        """Summarizes text. If row is specified, returns string. Otherwise modifies data and returns self."""
        if row is not None:
            text = self._df.iloc[row]["content"]
            summary = summarize_text(text, model=model)
            print("\nSummary:\n")
            print(summary)
            return summary

        summaries = []
        for text in self._df["content"]:
            summaries.append(summarize_text(text, model=model))
            
        self._df["summary"] = summaries
        return self

    def visualize(self, chart_type, column):
        """Visualizes data abstracting away Matplotlib."""
        if chart_type == "bar":
            plot_bar(self._df[column].tolist(), column)
        return self

    def filter_by(self, column, value):
        filtered = self._df[self._df[column] == value]
        return SentiData(dataframe=filtered.copy())

    def by_location(self, value):
        return self.filter_by("location", value)

    def by_category(self, value):
        return self.filter_by("category", value)

    def aggregate(self, column):
        """Returns aggregation as a standard python dictionary."""
        return self._df[column].value_counts(normalize=True).to_dict()

    def export(self, path):
        self._df.to_csv(path, index=False)
        return self

    def head(self, n=5):
        """Returns top n rows as a list of dictionaries to abstract Pandas."""
        import json
        return json.loads(self._df.head(n).to_json(orient='records', date_format='iso'))

    @property
    def data(self):
        """Exposes raw data as list of dicts."""
        import json
        return json.loads(self._df.to_json(orient='records', date_format='iso'))

    def __getitem__(self, key):
        return self._df[key].tolist()

    def topic_summary(self, model="mistral"):
        if "review_topic" not in self._df.columns:
            print("No topics found. Please run extract_topics() first.")
            return {}

        topics = self._df["review_topic"].unique()
        summaries = {}
        for topic in topics:
            topic_reviews = self._df[self._df["review_topic"] == topic]["content"]
            combined_text = " ".join(topic_reviews.tolist())
            summary = summarize_text(combined_text, model=model)
            summaries[topic] = summary
            print(f"\nTopic {topic}\nSummary: {summary}")
        return summaries

    def topic_sentiment(self):
        if "review_topic" not in self._df.columns or "sentiment" not in self._df.columns:
            return {}
            
        matrix = (
            self._df
            .groupby(["review_topic", "sentiment"])
            .size()
            .unstack(fill_value=0)
        )
        print("\nTopic Sentiment Matrix\n")
        matrix_dict = matrix.to_dict('index')
        print(matrix_dict)
        return matrix_dict
