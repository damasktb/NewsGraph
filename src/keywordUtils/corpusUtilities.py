import nltk
import numpy as np
import string
import unicodedata

from cStringIO import StringIO
from stop_words import get_stop_words
from sys import maxunicode
from unidecode import unidecode

from graphKnowledge import NewsGraphKnowledge

def tokenize(doc, knowledge=True, ltze=True):
	wnl = nltk.WordNetLemmatizer()
	knowledge = NewsGraphKnowledge()
	tokens = []
	entities = []
	# Don't transform letter case until after entity recognition, or it will fail.
	punctuation = [i for i in xrange(maxunicode)
		if unicodedata.category(unichr(i)).startswith('P')]

	stopWords = set(get_stop_words("en"))

	prevTree = ""
	for sentence in preprocess(doc):
		if prevTree:
			tokens.append(prevTree.strip())
			entities.append(prevTree.strip())
			prevTree = ""
		for chunk in nltk.ne_chunk(sentence, binary=False):
			if isinstance(chunk, nltk.Tree):
				t = " ".join(ent[0] for ent in chunk.leaves()).strip()
				prevTree += t+" "
			else:
				if prevTree:
					tokens.append(prevTree.strip())
					#if t not in entities: #No point querying KnowledgeGraph multiple times
					entities.append(prevTree.strip())
					prevTree = ""
				t = chunk[0].lower()
				if ltze: 
					t = wnl.lemmatize(t)
				if t not in stopWords and not t.isdigit():
					t = string.strip(t, string.punctuation)
					tokens.append(t)
	
	aliases = knowledge.aliasEntities(entities)
	entities = [aliases.get(e, e) for e in entities]
	return tokens, entities

def preprocess(doc):
	sentences = nltk.sent_tokenize(doc)
	words = [nltk.word_tokenize(s) for s in sentences]
	return [nltk.pos_tag(w) for w in words]
