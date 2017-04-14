import nltk
import string
import unicodedata

from lxml import etree

from cStringIO import StringIO
from stop_words import get_stop_words
from sys import maxunicode
from unidecode import unidecode
from goose import Goose

from graphKnowledge import NewsGraphKnowledge

gooseExtractor = Goose()

def tokenize(doc, knowledge=True, ltze=False):
	wnl = nltk.WordNetLemmatizer()
	knowledge = NewsGraphKnowledge()
	tokens = []
	entities = []
	# Don't transform letter case until after entity recognition
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
				# Keep accumalating named entity chunks and appending, until
				# we reach a non-NE chunk which signals the end of the previous.
				if prevTree:
					tokens.append(prevTree.strip())
					entities.append(prevTree.strip())
					prevTree = ""
				t = chunk[0].lower()
				if ltze: 
					t = wnl.lemmatize(t)
				if t not in stopWords and not t.isdigit():
					t = string.strip(t, string.punctuation)
					tokens.append(t)
	
	aliases, freqs = knowledge.aliasEntities(entities)
	entities = [aliases.get(e, e) for e in entities]
	return tokens, entities, freqs

def parseHTML(article):
	article = gooseExtractor.extract(url=article.url)
	return article.cleaned_text, article.meta_description

def preprocess(doc):
	sentences = nltk.sent_tokenize(doc)
	words = [nltk.word_tokenize(s) for s in sentences]
	return [nltk.pos_tag(w) for w in words]