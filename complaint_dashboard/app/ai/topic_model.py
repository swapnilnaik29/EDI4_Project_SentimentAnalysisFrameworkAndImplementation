import logging
import hashlib
import json
import numpy as np
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# 1. Load Sentence Transformers
# ---------------------------------------------------------
_embedding_model = None
try:
    from sentence_transformers import SentenceTransformer
    # Small fast embedding model running locally on CPU
    _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("SentenceTransformer (all-MiniLM-L6-v2) loaded successfully.")
except Exception as e:
    logger.warning(f"Could not load SentenceTransformer ({e}). Using deterministic mock embeddings.")

def get_embedding(text: str) -> List[float]:
    """Generates a 384-dimensional embedding vector for the text."""
    if _embedding_model:
        try:
            emb = _embedding_model.encode(text)
            return emb.tolist()
        except Exception as e:
            logger.error(f"Error in SentenceTransformer encoding: {e}")
            
    # Deterministic fallback hashing: generate a consistent 384-float vector
    h = hashlib.sha256(text.encode("utf-8")).digest()
    np.random.seed(int.from_bytes(h[:4], byteorder="big"))
    vec = np.random.normal(0, 1, 384)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()

# ---------------------------------------------------------
# 2. Check for BERTopic and related ML dependencies
# ---------------------------------------------------------
HAS_BERTOPIC = False
try:
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    HAS_BERTOPIC = True
    logger.info("BERTopic, UMAP, and HDBSCAN imported successfully.")
except ImportError:
    logger.info("BERTopic/HDBSCAN not fully available. Fallback to scikit-learn clustering.")

# ---------------------------------------------------------
# 3. Clustering and Topic Modeling
# ---------------------------------------------------------
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

async def cluster_complaints(complaints: List[Dict[str, Any]]) -> Tuple[List[int], Dict[int, Dict[str, Any]]]:
    """
    Groups a list of complaints into topics.
    Returns:
        - List of topic IDs corresponding to each input complaint
        - Dictionary mapping topic_id to { "label": str, "keywords": list }
    """
    if not complaints:
        return [], {}
        
    n_docs = len(complaints)
    texts = [c["cleaned_text"] or c["complaint_text"] for c in complaints]
    
    # Pre-calculate embeddings
    embeddings = np.array([get_embedding(t) for t in texts])
    
    # Under low-data situations (e.g. less than 8 complaints), we place them in a single topic
    # or perform a basic cosine distance threshold grouping.
    if n_docs < 6:
        # Too small for clustering, put all under General topic
        topic_ids = [0] * n_docs
        keywords = extract_keywords_for_docs(texts, top_n=5)
        # Fetch label dynamically
        from app.ai.llm import generate_topic_label
        label = await generate_topic_label(keywords, texts)
        topic_info = {0: {"label": label, "keywords": keywords}}
        return topic_ids, topic_info

    # Initialize clustering parameters
    # Let number of clusters scale with complaints
    n_clusters = max(2, min(n_docs // 4, 10))
    
    topic_ids = []
    topic_info = {}
    
    # Try BERTopic first if available
    bertopic_worked = False
    if HAS_BERTOPIC and n_docs >= 15:
        try:
            # Setup custom low-dimension parameters for small CPU-based clustering
            umap_model = UMAP(n_neighbors=min(15, n_docs - 1), n_components=5, min_dist=0.0, metric='cosine', random_state=42)
            hdbscan_model = HDBSCAN(min_cluster_size=min(5, n_docs // 3), metric='euclidean', cluster_selection_method='eom', prediction_data=True)
            
            # Disable vectorizer lowercase if already cleaned
            topic_model = BERTopic(
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                embedding_model=_embedding_model,
                calculate_probabilities=False,
                verbose=False
            )
            
            topics, _ = topic_model.fit_transform(texts, embeddings)
            topic_ids = topics
            
            # Map BERTopic output to our info structure
            unique_topics = set(topics)
            from app.ai.llm import generate_topic_label
            
            for t_id in unique_topics:
                # -1 is noise in HDBSCAN/BERTopic
                if t_id == -1:
                    topic_info[-1] = {"label": "Uncategorized Issues", "keywords": ["general", "complaint", "bank"]}
                    continue
                    
                # Extract keywords from BERTopic representation
                rep_words = [word for word, _ in topic_model.get_topic(t_id)[:5]]
                rep_docs = topic_model.get_representative_docs(t_id) or [texts[i] for i, t in enumerate(topics) if t == t_id]
                
                label = await generate_topic_label(rep_words, rep_docs)
                topic_info[t_id] = {"label": label, "keywords": rep_words}
                
            bertopic_worked = True
            logger.info("Clustered using BERTopic.")
        except Exception as e:
            logger.warning(f"BERTopic clustering failed ({e}). Falling back to KMeans.")
            
    if not bertopic_worked:
        # Standard KMeans Fallback
        try:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
            labels = kmeans.fit_predict(embeddings)
            topic_ids = [int(l) for l in labels]
            
            # Extract keywords via TF-IDF per cluster
            from app.ai.llm import generate_topic_label
            for c_id in range(n_clusters):
                cluster_indices = [i for i, l in enumerate(topic_ids) if l == c_id]
                cluster_texts = [texts[i] for i in cluster_indices]
                
                keywords = extract_keywords_for_docs(cluster_texts, top_n=5)
                label = await generate_topic_label(keywords, cluster_texts)
                
                topic_info[c_id] = {
                    "label": label,
                    "keywords": keywords
                }
            logger.info("Clustered using scikit-learn KMeans.")
        except Exception as e:
            logger.error(f"KMeans clustering failed ({e}). Assigning all to topic 0.")
            topic_ids = [0] * n_docs
            keywords = ["service", "transaction", "bank", "account", "delay"]
            topic_info = {0: {"label": "General Operations", "keywords": keywords}}
            
    return topic_ids, topic_info

def extract_keywords_for_docs(docs: List[str], top_n: int = 5) -> List[str]:
    """Helper to extract top TF-IDF keywords from a set of documents."""
    try:
        # Standard TF-IDF vectorization
        vectorizer = TfidfVectorizer(stop_words='english', max_features=50)
        tfidf_matrix = vectorizer.fit_transform(docs)
        feature_names = vectorizer.get_feature_names_out()
        
        # Average TF-IDF weights across documents
        avg_weights = np.mean(tfidf_matrix.toarray(), axis=0)
        top_indices = np.argsort(avg_weights)[::-1][:top_n]
        
        keywords = [str(feature_names[i]) for i in top_indices]
        if not keywords:
            raise ValueError()
        return keywords
    except Exception:
        # Fallback to simple token counting if TF-IDF fails
        words = []
        for doc in docs:
            words.extend([w.lower() for w in doc.split() if len(w) > 3])
        # Count frequency
        from collections import Counter
        common = Counter(words).most_common(top_n)
        return [w for w, c in common] if common else ["issue", "support", "help"]

def match_closest_topic(embedding: List[float], topic_centroids: Dict[int, List[float]]) -> int:
    """
    Finds the closest topic ID to a new complaint's embedding.
    Calculates cosine similarity against all topic centroids.
    """
    if not topic_centroids:
        return 0
        
    emb_arr = np.array(embedding)
    best_id = 0
    best_sim = -1.0
    
    for t_id, centroid in topic_centroids.items():
        cent_arr = np.array(centroid)
        # Cosine similarity
        norm_a = np.linalg.norm(emb_arr)
        norm_b = np.linalg.norm(cent_arr)
        if norm_a == 0 or norm_b == 0:
            sim = 0.0
        else:
            sim = np.dot(emb_arr, cent_arr) / (norm_a * norm_b)
            
        if sim > best_sim:
            best_sim = sim
            best_id = t_id
            
    return best_id
