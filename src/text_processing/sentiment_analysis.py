import torch
import pandas as pd
from transformers import pipeline, AutoTokenizer

device = 0 if torch.cuda.is_available() else -1

MODEL_NAME = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"

sentiment_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
sentiment_pipe = pipeline(
    "text-classification",
    model=MODEL_NAME,
    tokenizer=sentiment_tokenizer,
    max_length=512,
    truncation=True,
    device=device,
)

CHUNK_TOKEN_BUDGET = 480  # leave headroom under the model's 512 limit for special tokens


# ---------------------------------------------------------------------------
# Generic batched scorer
# ---------------------------------------------------------------------------

def score_texts(texts: list, batch_size: int = 16) -> list:
    """Scores a list of texts for sentiment using batched model inference.

    :param texts: The texts to score. Empty/whitespace-only entries are
        skipped and scored as None without a model call.
    :param batch_size: The number of texts sent to the pipeline per batch.
    :return: A list of {"label": str, "score": float} dicts, same order
        and length as ``texts``.
    """
    results = [None] * len(texts)
    to_score, index_map = [], []

    for i, t in enumerate(texts):
        if t and t.strip():
            to_score.append(t)
            index_map.append(i)
        else:
            results[i] = {"label": None, "score": None}

    if to_score:
        raw = sentiment_pipe(to_score, batch_size=batch_size)
        for idx, r in zip(index_map, raw):
            results[idx] = {"label": r["label"], "score": r["score"]}

    return results


# ---------------------------------------------------------------------------
# Whole-article sentiment
# ---------------------------------------------------------------------------

def chunk_article(text: str, max_tokens: int = CHUNK_TOKEN_BUDGET) -> list:
    """Splits an article into token-budget-respecting chunks using the model's tokenizer.

    :param text: The article text to split.
    :param max_tokens: The maximum number of tokens per chunk.
    :return: A list of decoded text chunks, each within the token budget.
    """
    token_ids = sentiment_tokenizer.encode(text, add_special_tokens=False)
    if not token_ids:
        return []
    chunks = []
    for i in range(0, len(token_ids), max_tokens):
        chunk_ids = token_ids[i:i + max_tokens]
        chunks.append(sentiment_tokenizer.decode(chunk_ids, skip_special_tokens=True))
    return chunks


def score_article(text: str) -> dict:
    """Scores a full article by chunking it and aggregating chunk-level sentiment.

    :param text: The full article text to score.
    :return: A dict with the confidence-weighted majority label, the average
        confidence for that label, the chunk count, and the per-chunk
        breakdown for inspection.
    """
    chunks = chunk_article(text)
    if not chunks:
        return {"label": None, "score": None, "n_chunks": 0, "chunk_results": []}

    chunk_results = score_texts(chunks)

    # weight each label's vote by that chunk's confidence score
    label_weights = {}
    for r in chunk_results:
        if r["label"] is None:
            continue
        label_weights[r["label"]] = label_weights.get(r["label"], 0.0) + r["score"]

    if not label_weights:
        return {"label": None, "score": None, "n_chunks": len(chunks), "chunk_results": chunk_results}

    top_label = max(label_weights, key=label_weights.get)
    avg_confidence = sum(r["score"] for r in chunk_results if r["label"] == top_label) / \
                     sum(1 for r in chunk_results if r["label"] == top_label)

    return {
        "label": top_label,
        "score": avg_confidence,
        "n_chunks": len(chunks),
        "chunk_results": chunk_results,
    }


# ---------------------------------------------------------------------------
# Batch runner for a DataFrame of articles
# ---------------------------------------------------------------------------

def score_dataframe(df: pd.DataFrame, text_col: str = "clean_content") -> pd.DataFrame:
    """Scores every article in a DataFrame and appends sentiment columns.

    :param df: The DataFrame of articles to score.
    :param text_col: The name of the column containing article text.
    :return: A copy of ``df`` with sentiment_label, sentiment_score, and
        sentiment_n_chunks columns added.
    """
    df = df.copy()
    results = [score_article(t) for t in df[text_col]]  # each call already batches internally per-article
    df["sentiment_label"] = [r["label"] for r in results]
    df["sentiment_score"] = [r["score"] for r in results]
    df["sentiment_n_chunks"] = [r["n_chunks"] for r in results]
    return df


if __name__ == "__main__":
    df = pd.read_pickle("sample_articles.pkl")  # columns: id, content, ...
    df["clean_content"] = df["content"].astype(str)  # plug in your clean_text() here

    df = score_dataframe(df)
    print(df[["id", "sentiment_label", "sentiment_score", "sentiment_n_chunks"]])