import re
import string
import nltk
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from pprint import pprint
from textblob import TextBlob, Word
import streamlit as st
import pandas as pd
# from pattern.search import search
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt

vectorizer = CountVectorizer(analyzer='word',
                             min_df=3,  # minimum required occurences of a word
                             stop_words='english',  # remove stop words
                             lowercase=True,  # convert all words to lowercase
                             token_pattern='[a-zA-Z0-9]{3,}',  # num chars > 3
                             max_features=500,
                             # max number of unique words. Build a vocabulary that only consider the top max_features ordered by term frequency across the corpus
                             )


def detect_polarity(text):
    return TextBlob(text).sentiment.polarity


@st.cache
def convert_df(my_df):
    return my_df.to_csv().encode('utf-8')


def clean_text(text):
    '''Make text lowercase, remove text in square brackets, remove punctuation and remove words containing numbers.'''
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub(r'\w*\d\w*', '', text)
    return text


#
# def lemmatizer(text):
#     sent = []
#     doc = nlp(text)
#     for word in doc:
#         sent.append(word.lemma_)
#     return " ".join(sent)


def get_top_n_words(corpus, n=None):
    vec = CountVectorizer(stop_words='english').fit(corpus)
    bag_of_words = vec.transform(corpus)
    sum_words = bag_of_words.sum(axis=0)
    words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
    words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
    return words_freq[:n]


def get_top_n_bigram(corpus, n=None):
    vec = CountVectorizer(ngram_range=(2, 2), stop_words='english').fit(corpus)
    bag_of_words = vec.transform(corpus)
    sum_words = bag_of_words.sum(axis=0)
    words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
    words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
    return words_freq[:n]


def get_top_n_trigram(corpus, n=None):
    vec = CountVectorizer(ngram_range=(3, 3), stop_words='english').fit(corpus)
    bag_of_words = vec.transform(corpus)
    sum_words = bag_of_words.sum(axis=0)
    words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
    words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
    return words_freq[:n]


def show_topics(vectorizer_, lda_model_, n_words=20):
    keywords = np.array(vectorizer_.get_feature_names())
    topic_keywords = []
    for topic_weights in lda_model_.components_:
        top_keyword_locs = (-topic_weights).argsort()[:n_words]
        topic_keywords.append(keywords.take(top_keyword_locs))
    return topic_keywords


def search_service(text):
    if re.search('service', text):
        return 'service'
    elif re.search('report', text) or re.search('reports', text) or re.search('Reports', text) or re.search('Results',
                                                                                                            text) or re.search(
            'Report', text) or re.search('result', text) or re.search('results', text):
        return 'report'
    elif re.search('experience', text):
        return 'experience'
    elif re.search('collection', text) or re.search('sample', text) or re.search('collected', text) or re.search(
            'blood', text) or re.search('come', text) or re.search('collect', text) or re.search('came', text):
        return 'sample collection'
    elif re.search('on time', text) or re.search('in time', text):
        return 'time'
    else:
        return 'other'
