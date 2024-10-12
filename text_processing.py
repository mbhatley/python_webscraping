import pandas as pd
import numpy as np
from transformers import pipeline
import spacy

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

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
        # Ensure input is a string
        text = str(text)

        # Remove new lines, tabs, and non-breaking spaces
        text = re.sub(r"\n|\t|\xa0", " ", text)

        # Remove "Listen x:xx" strings
        text = re.sub(r"Listen \d+:\d+\s?", "", text)

        # Replace numbers with commas (removes commas from numbers)
        text = re.sub(r"\b\d+,\d+\b", lambda x: x.group().replace(",", ""), text)

        # Replace contractions with expanded forms
        contractions_dict = {
            "won't": "will not", "can't": "cannot", "i'm": "i am", "he's": "he is", "she's": "she is",
            "it's": "it is", "we're": "we are", "they're": "they are", "isn't": "is not",
            "aren't": "are not", "wasn't": "was not", "weren't": "were not", "hasn't": "has not",
            "haven't": "have not", "hadn't": "had not", "doesn't": "does not", "don't": "do not",
            "didn't": "did not", "couldn't": "could not", "wouldn't": "would not", "shouldn't": "should not",
            "mustn't": "must not", "let's": "let us", "i'll": "i will", "you'll": "you will",
            "he'll": "he will", "she'll": "she will", "we'll": "we will", "they'll": "they will",
            "i'd": "i would", "you'd": "you would", "he'd": "he would", "she'd": "she would",
            "we'd": "we would", "they'd": "they would", "i've": "i have", "you've": "you have",
            "we've": "we have", "they've": "they have", "who's": "who is", "what's": "what is",
            "where's": "where is", "how's": "how is", "n't": " not", "'s": " is", "'d": " would",
            "'ll": " will", "'m": " am", "'ve": " have", "'re": " are"
        }

        contractions_pattern = re.compile(r'\b({})\b'.format('|'.join(map(re.escape, contractions_dict.keys()))), re.IGNORECASE)

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