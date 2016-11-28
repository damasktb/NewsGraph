import feedparser

import newspaper
from newspaper import Article as RawArticle

from newsSerialiser import *

import uuid
from corpusUtilities import *
from graphObjects import *

import itertools

import pytz

import datetime

from tqdm import tqdm

from collections import Counter
import operator 

from time import strftime

import lxml.etree as ET


news_graph_knowledge = NewsGraphKnowledge()

# Don't sublclass from newspaper.article as objects instantiated from
# this class must be serialisable with cPickle (...no lxml)
class Article:
	def __init__(self, article, id, feed, defer=None):
		self.title = article.title
		self.text = article.text
		self.html = article.article_html
		try:
			self.publish_date = article.publish_date.replace(tzinfo=pytz.UTC)
		except AttributeError as e:
			self.publish_date = datetime.datetime.today()

		self.summary = article.summary
		self.url = article.url
		self.img = article.top_image
		self.uuid = id
		self.feed = feed
		self.tokens, self.entities = tokenize(
			self.title +" "+ self.text,
			news_graph_knowledge,
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
			return self.text.lower().count(term.lower())
		else: 
			return freq

	def containsTerm(self, term):
		return term.lower() in self.text.lower()

class ArticleCollection:
	

	def __init__(self, urls):
		# datetime.datetime as a dictionary key gives an 
		# implicit ordering even though dict is unordered
		self.collection_by_id = {}
		self.article_count = len(urls)
		# self.top_collection_entities = Counter()
		# self.collection_entities = {}

		print "Creating Collection"
		for url, feed_name in tqdm(urls):
			article = RawArticle(url, keep_article_html=True)
			article.download()
			article.parse()
			article_id = uuid.uuid1()

			processed_article = Article(article, article_id, feed_name)
			self.collection_by_id[article_id] = processed_article
			# for e in processed_article.entities:
			# 	self.top_collection_entities[e] += 1
			# 	update = self.collection_entities.get(e, [])
			# 	update.append(processed_article)
			# 	self.collection_entities[e] = update

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
		for term in (article.title+article.text[:50]).split():
			vector[term] = self.tf_idf(term, article_id)
		return dict(sorted(vector.iteritems(), key=operator.itemgetter(1), reverse=True)[:top_n])

	def entity_tf_idf_vector(self, article_id, top_n=-1):
		vector = {}
		article = self.article(article_id)
		for i, term in enumerate(article.entities[:len(article.entities)/2]):
			tfidf = self.tf_idf(term, article_id)
			if tfidf:
				vector[term] = tfidf * 1/(1+i/10.0)
		return dict(sorted(vector.iteritems(), key=operator.itemgetter(1), reverse=True)[:top_n])

	def top_article_keywords(self, top_n=10):
		ret = {}
		for id, article in self.collection_by_id.iteritems():
			for entity in self.entity_tf_idf_vector(id, top_n):
				update = ret.get(entity, [])
				update.append(article)
				ret[entity] = update
		return ret


read_cache = True	
write_cache = False

cln = None
if read_cache:
	rd = CacheReader()
	cln = rd.read()
else:
	feeds = ['http://www.theguardian.com/uk-news/rss']
	urls = []
	print "Fetching RSS Feed(s)"
	for feed in feeds:
		feed = feedparser.parse(feed)
		for item in feed["items"][:100]:
			urls.append((item["link"], feed["channel"]["title"]))
	cln = ArticleCollection(urls)

if write_cache:
	wr = CacheWriter(strftime("%Y%m%d-%H%M%S")+".ng")
	wr.write(cln)

e_map = cln.top_article_keywords(4)
top_25 = sorted(e_map.iteritems(), key=lambda (k,a): len(a), reverse=True)[:25]
subsumed = {}
for pair1, pair2 in itertools.combinations(top_25, 2):
	kw1, articles1 = pair1[0], set(pair1[1])
	kw2, articles2 = pair2[0], set(pair2[1])
	unique = len(articles1.difference(articles2))/float(len(articles1))
	print "Comparing ", kw1, " and ", kw2, ": ", str(unique)
	if unique < 0.5:
		print kw1, " subsumed by ", kw2
		subsumed[kw1] = kw2

new_top = {}
for (k, articles) in top_25:
	while k in subsumed:
		print k, " subsumed by ", subsumed[k]
		k = subsumed[k]
	
	arts_for_keyword = new_top.get(k, set())
	arts_for_keyword.update(articles)
	new_top[k] = arts_for_keyword

node_lookup = {}
links = []
nodes = []
multiedge_counts = {}

lines_for_article = {}

for i, (e, articles) in enumerate(new_top.iteritems()):
	if len(articles) > 4:
		sorted_nodes = sorted(articles, key=lambda a:a.publish_date)
		print e
		for a in sorted_nodes:
			print "-", a.title
		for n, a in enumerate(sorted_nodes):
			node_lookup[a] = node_lookup.get(a, len(node_lookup.keys()))
			lines = lines_for_article.get(a, [])
			lines.append(e)
			lines_for_article[a] = lines

		for n in range(len(sorted_nodes)-1):
			source = node_lookup[sorted_nodes[n]]
			target = node_lookup[sorted_nodes[n+1]]
			count = multiedge_counts.get((source, target), 0)+1
			multiedge_counts[(source, target)] = count
			
			links.append({
				"source": source,
				"target": target,
				"count": count,
				"line": e,
			})

nodes = [{"name": a[0].title, "lines":lines_for_article[a[0]]} for a in sorted(node_lookup.iteritems(), key=lambda x:x[1])]

ng = NewsGraph(nodes, links, lines_for_article)


