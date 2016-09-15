#!/usr/bin/env python
# -*- coding: utf-8 -*-
from corpusUtilities import *
from corpusTFIDF import *

from nltk.corpus import stopwords

import regex as re

from sklearn.feature_extraction.text import TfidfVectorizer

def tokenize(txt):
	txt = txt.lower()
	# txt = re.sub(ur"-[\r\n]+", "", txt)    # Try and 'glue' hyphenated line-broken words back together
	# txt = re.sub(ur"[\r?\n]+", " ", txt)   # Get rid of newline characters
	txt = re.sub(ur"[^\P{P}-']+", " ", txt) # Get rid of punctuation classes
	txt = txt.split(" ")
	#ignore = stopwords.words("english")
	txt = filter(lambda w: not w.isnumeric(), txt)
	return " ".join(txt)

token_dict = {	"facebook": tokenize(facebookText),
			 }

tfidf = TfidfVectorizer(stop_words='english')
tfs = tfidf.fit_transform(token_dict.values())

feature_names = tfidf.get_feature_names()
response = tfidf.fit_and_transform(tokenize(twitterText).split(" "))
for col in response.nonzero()[1]:
    print feature_names[col], ' - ', response[0, col]