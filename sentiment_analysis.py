# -*- coding: utf-8 -*-
"""DSLab assignment.ipynb

Automatically generated by Colaboratory.

**Imports**
"""

!python -m spacy download it_core_news_sm

import os
import re
import csv
import time
import spacy
import numpy as np
import string
import collections
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import ItalianStemmer

from sklearn.svm import SVC
from sklearn.svm import LinearSVC     
from sklearn.utils import shuffle
from sklearn.metrics import f1_score
from sklearn.linear_model import SGDClassifier
from sklearn.decomposition import TruncatedSVD
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

"""**Parameters**"""

nltk.download('stopwords')
stop = set(stopwords.words('italian') + ['l\'']) 
if 'non' in stop: stop.remove('non')
if 'ne' in stop: stop.remove('ne')

REPLACE_NO_SPACE = re.compile("[.;:!\'?,\"()\[\]]")
reg = re.compile("[0-9]<.*?>")
nlp = spacy.load('it_core_news_sm')
sns.set(style="darkgrid")
sns.set(font_scale=1.3)

"""**Data preprocessing**"""

def get_lemm_text(reviews):
  lemm_reviews = []
  for review in nlp.pipe(reviews, disable=["tagger", "parser"]):
    clean = (' '.join([l.lemma_.lower() for l in review if str(l) not in string.punctuation
                      and not reg.match(str(l))]))
    lemm_reviews.append(clean)
  return lemm_reviews

def stemm(reviews):
  stemm_reviews = []
  stemmer = ItalianStemmer()
  for review in reviews:
    clean = (' '.join([stemmer.stem(w) for w in review]))
    stemm_reviews.append(clean)  
  return stemm_reviews

def clean_text(reviews):
  clean_reviews = []
  for review in reviews:
    clean = (' '.join(w for w in review.split() if w not in stop_words and not reg.match(w)))
    clean = REPLACE_NO_SPACE.sub("", clean.lower())
    clean_reviews.append(clean)
  return clean_reviews

"""**Data reading and preparation**"""

dev_set = pd.read_csv("./data/development.csv")
test_set = pd.read_csv("./data/evaluation.csv")

X = [t for t in dev_set['text']]
y = [0 if l == 'pos' else 1 for l in dev_set['class']] 
 
X_test = [t for t in test_set['text']]

#### Clean and preprocess data ####
X_preproc = get_lemm_text(X)
X_test_preproc = get_lemm_text(X_test)

"""**Vectorization**"""

#### Vectorization ####
# cv = CountVectorizer(binary=True, ngram_range=(1, 2), stop_words=stop, analyzer='word')
cv = TfidfVectorizer(analyzer='word', stop_words=stop, ngram_range=(1, 2))
cv.fit(X_preproc)
X = cv.transform(X_preproc)
X_test = cv.transform(X_test_preproc)

"""**Plot most frequent ngrams**"""

word_freq = dict(zip(cv.get_feature_names(), np.asarray(X.sum(axis=0)).ravel()))
word_counter = collections.Counter(word_freq)
word_counter_df = pd.DataFrame(word_counter.most_common(10), columns = ['word', 'freq'])
fig, ax = plt.subplots(figsize=(12, 10))
sns.barplot(x="word", y="freq", data=word_counter_df, palette="PuBuGn_d", ax=ax)
plt.show();

"""**Split development set**"""

X, y = shuffle(X, y)
X_train, X_val, y_train, y_val = train_test_split(X, y, train_size = 0.75)

"""**Logistic Regression model**"""

c = 0.01
lr = LogisticRegression(C=c, max_iter=1000)
start_time = time.time()
lr.fit(X_train, y_train)
acc = f1_score(y_val, lr.predict(X_val), average='weighted')
print("--- %s seconds ---" % (time.time() - start_time))
print("### LogisticRegression### : Accuracy for C = %s: %s" % (c, acc))

"""**LinearSVC model**"""

c = 0.001
svm = LinearSVC(C=c)
start_time = time.time()
svm.fit(X_train, y_train)
acc = f1_score(y_val, svm.predict(X_val), average='weighted')
print("--- %s seconds ---" % (time.time() - start_time))
print("### LinearSVC ### : Accuracy for C = %s: %s" % (c, acc))

"""**Algorithm GridSearch**"""

lr_params = {'C':[0.01, 0.05, 0.25, 0.5, 1]}

lr = LogisticRegression(max_iter = 1000)
lr_clf = GridSearchCV(lr, lr_params, cv = 5)
start_time = time.time()
lr_clf.fit(X, y)
print("--- %s seconds ---" % (time.time() - start_time))
print("### LogisticRegression ###: C = %s, score = %s" % (lr_clf.best_params_, lr_clf.best_score_))

svm_params = {'C': [0.01, 0.05, 0.25, 0.5, 1]}
svm = LinearSVC()
svm_clf = GridSearchCV(svm, svm_params, cv = 5)
start_time = time.time()
svm_clf.fit(X, y)
print("--- %s seconds ---" % (time.time() - start_time))
print("### LinearSVC ###: C = %s, score = %s" % (svm_clf.best_params_, svm_clf.best_score_))

"""**Test on evaluation set and write output**"""

if lr_clf.best_score_ > svm_clf.best_score_:
  best_model = LogisticRegression(C = lr_clf.best_params_['C'], max_iter = 1000)
else:
  best_model = LinearSVC(C = svm_clf.best_params_['C'])

##### Predict test set labels #####
best_model.fit(X, y)

output = best_model.predict(X_test)
output = ['pos' if x == 0 else 'neg' for x in output]

with open("out.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(['Id', 'Predicted'])
    for i in range(len(output)):
        writer.writerow([i, output[i]])
    f.close()
