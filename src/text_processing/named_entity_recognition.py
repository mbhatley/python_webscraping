import spacy
import pandas as pd

nlp = spacy.load("en_core_web_trf")

DEFAULT_LABELS = ("ORG", "GPE", "PERSON")


def extract_entities(article_ids: list, texts: list, labels=DEFAULT_LABELS, batch_size: int = 8) -> pd.DataFrame:
    """Extracts named entity mentions from a batch of article texts.

    :param article_ids: The article id aligned with each text in ``texts``.
    :param texts: The article texts to run entity recognition over.
    :param labels: The spaCy entity labels to keep (others are discarded).
    :param batch_size: The number of texts processed per ``nlp.pipe`` batch.
    :return: A DataFrame with one row per entity mention, columns
        article_id, mention_text, label, start_char, end_char.
    """
    rows = []
    for article_id, doc in zip(article_ids, nlp.pipe(texts, batch_size=batch_size)):
        for ent in doc.ents:
            if ent.label_ in labels:
                rows.append({
                    "article_id": article_id,
                    "mention_text": ent.text.strip(),
                    "label": ent.label_,
                    "start_char": ent.start_char,
                    "end_char": ent.end_char,
                })
    return pd.DataFrame(rows)


def entity_mention_counts(entities_df: pd.DataFrame) -> pd.DataFrame:
    """Counts raw entity mention frequency, before any alias resolution.

    :param entities_df: The entity mentions DataFrame produced by ``extract_entities``.
    :return: A DataFrame of mention_text, label, and mention_count, sorted
        by mention_count descending.
    """
    if entities_df.empty:
        return entities_df
    return (
        entities_df.groupby(["mention_text", "label"])
        .size()
        .reset_index(name="mention_count")
        .sort_values("mention_count", ascending=False)
    )


if __name__ == "__main__":
    df = pd.read_pickle("sample_articles.pkl")  # columns: id, clean_content, ...
    entities_df = extract_entities(df["id"].tolist(), df["clean_content"].tolist())

    print(entities_df.head(20))
    print(entity_mention_counts(entities_df).head(10))