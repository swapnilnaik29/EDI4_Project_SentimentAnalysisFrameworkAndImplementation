from transformers import pipeline
import torch
from sentence_transformers import SentenceTransformer


class ModelManager:

    _models = {}

    @staticmethod
    def get_device():
        return 0 if torch.cuda.is_available() else -1

    @classmethod
    def get_sentiment_model(cls):

        if "sentiment" not in cls._models:

            cls._models["sentiment"] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment",
                device=cls.get_device()
            )

        return cls._models["sentiment"]

    @classmethod
    def get_embedding_model(cls):

        if "embedding" not in cls._models:

            device = "cuda" if torch.cuda.is_available() else "cpu"

            cls._models["embedding"] = SentenceTransformer(
                "all-MiniLM-L6-v2",
                device=device
            )

        return cls._models["embedding"]

    @classmethod
    def get_toxicity_model(cls):
        if "toxicity" not in cls._models:
            cls._models["toxicity"] = pipeline(
                "text-classification",
                model="martin-ha/toxic-comment-model",
                device=cls.get_device()
            )
        return cls._models["toxicity"]

    @classmethod
    def get_ner_model(cls):
        if "ner" not in cls._models:
            cls._models["ner"] = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple",
                device=cls.get_device()
            )
        return cls._models["ner"]
