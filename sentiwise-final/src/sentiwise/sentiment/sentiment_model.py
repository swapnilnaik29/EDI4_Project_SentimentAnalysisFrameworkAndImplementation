from tqdm import tqdm
from sentiwise.models.model_manager import ModelManager


def predict_sentiment(texts, batch_size=32):

    sentiment_model = ModelManager.get_sentiment_model()

    labels = []

    for i in tqdm(range(0, len(texts), batch_size)):

        batch = texts[i:i+batch_size]

        results = sentiment_model(batch)

        for r in results:

            label = r["label"]

            if label == "LABEL_0":
                labels.append("negative")

            elif label == "LABEL_1":
                labels.append("neutral")

            else:
                labels.append("positive")

    return labels
