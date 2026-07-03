from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from sentiwise.models.model_manager import ModelManager


def extract_topics(texts, size=3):

    embedder = ModelManager.get_embedding_model()

    embeddings = embedder.encode(texts, show_progress_bar=True)

    # cluster reviews
    kmeans = KMeans(n_clusters=size, random_state=42)

    clusters = kmeans.fit_predict(embeddings)

    # extract keywords for each cluster
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=2000
    )

    X = vectorizer.fit_transform(texts)

    words = vectorizer.get_feature_names_out()

    topics = []

    for topic_id in range(size):

        cluster_indices = [i for i, c in enumerate(clusters) if c == topic_id]

        cluster_matrix = X[cluster_indices]

        scores = cluster_matrix.mean(axis=0).A1

        top_indices = scores.argsort()[::-1]

        for idx in top_indices:
            topic_word = words[idx]
            if topic_word not in topics:
                topics.append(topic_word)
                break

    return clusters, topics
