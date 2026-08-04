import ftfy
import re


def clean_text(text: str) -> str:
    """Normalizes text encoding and whitespace for downstream processing.

    :param text: The raw text to clean.
    :return: The cleaned, whitespace-normalized string.
    """
    text = str(text)
    text = ftfy.fix_text(text)  # repairs mojibake before anything else
    text = re.sub(r"\n|\t|\xa0", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()