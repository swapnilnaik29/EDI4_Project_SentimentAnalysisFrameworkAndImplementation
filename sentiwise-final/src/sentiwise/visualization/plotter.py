import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter


def plot_bar(data_list, column_name="Data"):
    """
    Plots a bar chart from a raw list of data.
    """
    counts = Counter(data_list)

    sns.barplot(
        x=list(counts.keys()),
        y=list(counts.values())
    )

    plt.title(f"{column_name} distribution")
    plt.show()


def plot_sentiment_by_location(data_dicts):
    """
    Plots sentiment by location using a list of dicts.
    """
    import pandas as pd
    
    # Internal usage of pandas is fine, as long as it's not exposed to the user
    df = pd.DataFrame(data_dicts)
    if "location" not in df.columns or "sentiment" not in df.columns:
        print("Missing required columns for this plot.")
        return

    table = df.groupby(["location", "sentiment"]).size().unstack()
    table.plot(kind="bar", stacked=True)

    plt.title("Sentiment by Location")
    plt.show()

def plot_time_series(time_series_data):
    """
    Plots a time series line chart from a list of dicts.
    Each dict should have 'timestamp' and 'sentiment_score'.
    """
    import pandas as pd
    
    if not time_series_data:
        print("No time series data provided.")
        return
        
    df = pd.DataFrame(time_series_data)
    
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df, x="timestamp", y="sentiment_score", marker="o")
    plt.title("Average Sentiment Score Over Time")
    plt.axhline(0, color='red', linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
