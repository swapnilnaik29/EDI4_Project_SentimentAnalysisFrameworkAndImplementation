import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from sentiwise.core.senti_data import SentiData
from sentiwise.visualization.plotter import plot_time_series

print("Loading data...")
data = SentiData(file_path="../data/reviews_dataset_large.csv")

print("\nRunning Advanced SentiWise analysis pipeline...")
# Chainable API without exposing Pandas
data.analyze_sentiment().detect_toxicity().extract_ner().extract_advanced(model="mistral")

print("\nSample Data (Top 1 Row Processed):")
print(json.dumps(data.head(1), indent=2, default=str))

print("\nPipeline execution complete!")
data.visualize("bar", "sentiment")
