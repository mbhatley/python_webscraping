import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
embedder = SentenceTransformer(EMBED_MODEL_NAME)


def compute_embeddings(texts: list) -> np.ndarray:
    """Encodes texts into embeddings for reuse in both storage and topic modeling.

    :param texts: The texts to embed.
    :return: An array of embedding vectors, one row per input text.
    """
    return embedder.encode(texts, show_progress_bar=True)


def build_topic_model(min_cluster_size: int = 25, n_neighbors: int = 15) -> BERTopic:
    """Builds a BERTopic model with UMAP dimensionality reduction and HDBSCAN clustering.

    :param min_cluster_size: The minimum HDBSCAN cluster size.
    :param n_neighbors: The number of neighbors used by UMAP.
    :return: An unfitted BERTopic model configured with the given clustering parameters.
    """
    umap_model = UMAP(
        n_neighbors=n_neighbors, n_components=5, min_dist=0.0,
        metric='cosine', low_memory=True, random_state=42,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=min_cluster_size, metric='euclidean',
        cluster_selection_method='eom', prediction_data=True,
    )
    return BERTopic(umap_model=umap_model, hdbscan_model=hdbscan_model, calculate_probabilities=False)


def fit_topics(texts: list, embeddings: np.ndarray, min_cluster_size: int = 25):
    """Fits a new topic model on a full corpus (for one-time historical backfills).

    :param texts: The document texts to fit the topic model on.
    :param embeddings: The precomputed embeddings aligned with ``texts``.
    :param min_cluster_size: The minimum HDBSCAN cluster size to use.
    :return: A tuple of (fitted topic_model, topic assignments per document,
        topic_info DataFrame).
    """
    topic_model = build_topic_model(min_cluster_size=min_cluster_size)
    topics, _ = topic_model.fit_transform(texts, embeddings)
    return topic_model, topics, topic_model.get_topic_info()


def assign_new_articles(topic_model: BERTopic, texts: list, embeddings: np.ndarray):
    """Assigns new articles to an existing fitted topic model without refitting.

    :param topic_model: The already-fitted BERTopic model.
    :param texts: The new document texts to assign topics to.
    :param embeddings: The precomputed embeddings aligned with ``texts``.
    :return: The topic assignment for each document in ``texts``.
    """
    topics, _ = topic_model.transform(texts, embeddings)
    return topics


def topics_over_time(topic_model: BERTopic, texts: list, timestamps: list, nr_bins: int = 48):
    """Computes topic frequency evolution across time bins.

    :param topic_model: The already-fitted BERTopic model.
    :param texts: The document texts corresponding to ``timestamps``.
    :param timestamps: The timestamp for each document in ``texts``.
    :param nr_bins: The number of time bins to group documents into.
    :return: A DataFrame of topic frequencies over time, as returned by
        BERTopic's ``topics_over_time``.
    """
    return topic_model.topics_over_time(docs=texts, timestamps=timestamps, nr_bins=nr_bins)


if __name__ == "__main__":
    df = pd.read_pickle("sample_articles.pkl")  # columns: id, clean_content, published_date

    embeddings = compute_embeddings(df["clean_content"].tolist())

    # NOTE: min_cluster_size=2 here is ONLY for sandboxing at tiny sample sizes -
    # do not carry this value forward to your real corpus.
    topic_model, topics, topic_info = fit_topics(
        df["clean_content"].tolist(), embeddings, min_cluster_size=2
    )

    df["topic"] = topics
    print(topic_info)
    print(df[["id", "topic"]])