import numpy as np
import math
from os.path import abspath

from cStringIO import StringIO

import string

import nltk
#from nltk.corpus import stopwords
from stop_words import get_stop_words
from graphKnowledge import *

import sys
import unicodedata

from unidecode import unidecode

def tokenize(doc, knowledge, ltze=True, extract_entities=False):
	wnl = nltk.WordNetLemmatizer()
	tokens = []
	entities = set()
	# Don't transform letter case until after entity recognition, or it will fail.
	punctuation = [i for i in xrange(sys.maxunicode) 
		if unicodedata.category(unichr(i)).startswith('P')]

	stopWords = set(get_stop_words("en"))
	prevTree = ""
	for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(doc)), binary=False):
		if isinstance(chunk, nltk.Tree):
			t = " ".join(ent[0] for ent in chunk.leaves())
			#TODO This is horrific
			prevTree = (prevTree+" "+t).strip()
		else:
			if prevTree:
				entities.add(prevTree)
				prevTree = ""

			t = chunk[0].lower()
			if ltze: 
				t = unicode(wnl.lemmatize(t))
			if t not in stopWords and not unicode.isnumeric(t):
				t = unicode.strip(t)
				tokens.append(t)
	
	aliases = knowledge.aliasEntities(entities)
	if aliases:
		entities = list(set(aliases.get(e, e) for e in entities))
	if extract_entities:
		return tokens, entities
	else:
		return tokens.extend(entities)

# class LevelStatistics:
# 	def __init__(self, word, spectra, dists, doc_words):
# 		self.doc_word_count = doc_words
# 		self.spectra = spectra
# 		n = len(spectra)
# 		if dists:
# 			self.distances = dists
# 			self.mean_d = np.mean(self.distances)
# 			self.mean_d_sq = np.mean(map(lambda d: d**2, self.distances))
# 			self.stdev_d = np.sqrt(self.mean_d_sq - (self.mean_d**2))

# 			sigma = self.stdev_d/self.mean_d
# 			p = n*1.0/self.doc_word_count
# 			sigma_nor = sigma/np.sqrt(1-p)
# 			avg_sigma_nor = ((2*n)-1)/((2*n)+2)
# 			stdev_avg_sigma_nor = 1.0/(np.sqrt(n)*2.8*math.pow(n,-0.865))
# 			self.c = stdev_avg_sigma_nor

# 	def C(self):
# 		try:
# 			return self.c
# 		except AttributeError:
# 			return 0


# class Spectra:
# 	def __init__(self, doc, exclude_stopwords=True):
# 		doc_tokens = tokenize(doc)
# 		self.level_statistics = {}
# 		self.all_spectra = {}
# 		all_dists = {}
# 		self.total = len(doc_tokens)
		
# 		for i, token in enumerate(doc_tokens):
# 			spectrum = self.all_spectra.get(token, [])
# 			spectrum.append(i)
# 			self.all_spectra[token] = spectrum
# 			if len(spectrum) == 1:
# 				all_dists[token] = []
# 			if len(spectrum) > 1:
# 				all_dists[token].append(spectrum[-1] - spectrum[-2])
# 		for token in doc_tokens:
# 			self.level_statistics[token] = LevelStatistics(token, self.all_spectra[token], all_dists[token], self.total)

# 	def levelStatistics(self, word):
# 		return self.level_statistics.get(word, None)

# 	def orderedLevelStatistics(self, top=-1):
# 		ols = []
# 		for token, levelstats in self.level_statistics.iteritems():
# 			c = levelstats.C()
# 			if c:
# 				ols.append((token, c))
# 		return sorted(ols, key=lambda o:o[1], reverse=True)[0:top]
