import pandas as pd
import numpy as np
from transformers import pipeline
import spacy

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity

from fuzzywuzzy import fuzz

# for text pre-processing
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk import FreqDist

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('stopwords')

class CleanScrapedContent:

    def __init__(self, threshold=85):

        self.summarizer = pipeline("summarization",
                                   model="pszemraj/pegasus-x-large-book-summary",
                                   tokenizer="pszemraj/pegasus-x-large-book-summary",
                                   max_length=1024, truncation=True)

        self.pipe = pipeline("text-classification",
                             model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
                             tokenizer="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
                             max_length=512, truncation=True, device=0)

        self.nlp = spacy.load("en_core_web_trf")

        self.stop_words = set(stopwords.words('english'))

        self.lemmatizer = WordNetLemmatizer()

        self.threshold = threshold

        self.token_pattern = re.compile(r'\b\w+\b')


    def clean_text(self, text):
        """
        Function that goes through text and cleans it up to make it easier to process
        :param text: Text to be cleaned
        :return: Cleaned text
        """
        # Remove new lines, tabs, and non-breaking spaces
        text = re.sub(r"\n|\t|\xa0", " ", str(text))

        # Remove "Listen x:xx " strings
        text = re.sub(r"Listen \d+:\d+\s?", "", text)

        # Replace numbers with commas
        text = re.sub(r"\b\d+,", lambda x: x.group().replace(",", ""), text)

        # Replace contractions
        contractions_pattern = re.compile(r"(\b\w+?(?:'[dtlm]|n't|'s|'ve|'re)\b)", re.IGNORECASE)
        contractions_dict = {
            "won't": "will not",
            "can't": "cannot",
            "n't": " not",
            "'s": " is",
            "'d": " would",
            "'ll": " will",
            "'m": " am",
            "'ve": " have",
            "'re": " are"
        }

        def replace_contractions(match):
            contraction = match.group(0).lower()
            return contractions_dict.get(contraction, contraction)

        text = contractions_pattern.sub(replace_contractions, text)

        # Replace multiple spaces with a single space
        text = re.sub(r"\s+", " ", text)

        return text.strip()


    def named_entity_extraction(self, text):
        """
        Function utilizing SpaCy to extract Named Entities from articles
        : param text: Text to be cleaned
        : return: Entities from text
        """

        token = self.nlp(text)
        entity = [ent.text for ent in token.ents if ent.label_ == 'ORG']
        entities = list(set(entity))
        entities = ', '.join(entities)

        return entities


    def tokenize_and_lemmatize(self, text):
        """
        Function to tokenize and lemmatize text for sentiment analysis
        : return: Lemmatized text
        """

        # Tokenize
        tokens = self.token_pattern.findall(text)

        # Remove stop words and lemmatize
        lemmas = [self.lemmatizer.lemmatize(word) for word in tokens if word not in self.stop_words]

        return ' '.join(lemmas)


    def sentiment(self, text):
        """
        Sentiment analyzer function from HuggingFace
        : return: Sentiment in the form of `positive`, `negative`, or `neutral`
        """

        sentiment_result = self.pipe(text)
        top_sentiment = max(sentiment_result, key = lambda x: x['score'])
        sentiments = top_sentiment['label']

        return sentiments


    def summary(self, text):
        """
        Must be run after sentiment
        :return: Summary of the article
        """

        text_length = len(text)
        max_len = min(int(0.3 * text_length), 600)
        min_len = min(max_len, 5)

        summary = self.summarizer(text, min_length=min_len, max_length=max_len, do_sample=False)

        summary = summary[0].get('summary_text', '')

        return summary