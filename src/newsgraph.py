import feedparser

import newspaper
from newspaper import Article as RawArticle

import uuid
from corpusUtilities import *
from graphObjects import *

import datetime
# import pickle

from tqdm import tqdm

from collections import Counter
import operator

from unidecode import unidecode

class Article:
	def __init__(self, article, id, defer=None):
		self.raw = article
		self.uuid = id
		self.tokens, self.entities = tokenize(
			article.title+" "+ article.text,
			ArticleCollection.news_graph_knowledge,
			extract_entities = True
		)
		self.word_count = len(self.tokens)
		self.term_frequency = {}

	def termFrequency(self, term):
		if not self.term_frequency:
			for word in self.tokens:
				current = self.term_frequency.get(word, 0)
				self.term_frequency[word] = current+1
		
		freq = self.term_frequency.get(term, 0)
		if freq == 0:
			return self.raw.text.lower().count(term.lower())
		else: 
			return freq

	def containsTerm(self, term):
		return term.lower() in self.raw.text.lower()

class ArticleCollection:
	news_graph_knowledge = NewsGraphKnowledge()

	def __init__(self, urls):
		# datetime.datetime as a dictionary key gives an 
		# implicit ordering even though dict is unordered
		self.collection_by_id = {}
		self.keywords = {}
		self.article_count = len(urls)
		self.top_collection_entities = Counter()

		print "Creating Collection"
		for url in tqdm(urls):
			article = RawArticle(url)
			article.download()
			article.parse()
			article_id = uuid.uuid1()

			self.collection_by_id[article_id] = Article(article, article_id, defer=None)

	def article(self, article_id):
		return self.collection_by_id.get(article_id, None)

	def idf(self, term):
		n_containing = 0
		for article in self.collection_by_id.values():
			if article.containsTerm(term):
				n_containing += 1
		return math.log(self.article_count/n_containing)

	def tf_idf(self, term, article_id):
		article = self.article(article_id)
		try:
			return article.termFrequency(term) * self.idf(term)
		except ZeroDivisionError:
			pass
			#Probably a whitespace/punctuation error
			#raise KeyError('Keyword "%s" does not exist in any article' % term)

	def tf_idf_vector(self, article_id, top_n=-1):
		vector = {}
		article = self.article(article_id)
		for term in set(article.tokens):
			vector[term] = self.tf_idf(term, article_id)
		return dict(sorted(vector.iteritems(), key=operator.itemgetter(1), reverse=True)[:top_n])

	def entity_tf_idf_vector(self, article_id, top_n=-1):
		vector = {}
		article = self.article(article_id)
		for term in article.entities:
			vector[term] = self.tf_idf(term, article_id)
		return dict(sorted(vector.iteritems(), key=operator.itemgetter(1), reverse=True)[:top_n])

feeds = { 'guardian': 'https://www.theguardian.com/uk-news/rss'} 
links = {}
print "Fetching RSS Feed"
for name in feeds:
	feed = feeds[name]
	links[name] = []
	feed = feedparser.parse(feed)
	for item in feed["items"][:75]:
		links[name].append(item["link"])

entity_map = {}
for name, urls in links.iteritems():
	cln = ArticleCollection(urls)
	for uuid, article in cln.collection_by_id.iteritems():
		for e in cln.entity_tf_idf_vector(uuid, 5).keys():
			put_back = entity_map.get(e, [])
			put_back.append(article)
			entity_map[e] = put_back

node_lookup = {}
links = []
nodes = []
multiedge_counts = {}
print "Building Graph"
for e, articles in entity_map.iteritems():
	if len(articles) > 1:
		print e
		sorted_nodes = [a for a in sorted(articles, key=lambda a:a.raw.publish_date)]
		for a in sorted_nodes:
			print "--", a.raw.title
			node_lookup[a] = node_lookup.get(a, len(node_lookup.keys()))

		for n in range(len(sorted_nodes)-1):
			source = node_lookup[sorted_nodes[n]]
			target = node_lookup[sorted_nodes[n+1]]
			count = multiedge_counts.get((source, target), 0)+1
			multiedge_counts[(source, target)] = count
			links.append({
				"source": source,
				"target": target,
				"count": count,
				"label": e.encode("utf8","ignore")
			})

nodes = [{"size": 10, "name": unidecode(a[0].raw.title)} for a in sorted(node_lookup.iteritems(), key=lambda x:x[1])]
ng = NewsGraph(nodes, links)