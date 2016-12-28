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

import collections
import operator 

from time import strftime

import lxml.etree as ET


news_graph_knowledge = NewsGraphKnowledge()

class NewsFeed:
	def __init__(self, feed_name):
		self.name = feed_name
		self.F_jc = collections.Counter() # Frequency of all terms in the channel
		self.n_jc = collections.Counter() # Number of documents in the channel which contain the term
		self.article_count = 0

	def addArticle(self, article):
		self.article_count += 1
		for e in article.entities:
			self.n_jc[e] += 1
			self.F_jc[e] += article.termFrequency(e)

	def finalise(self):
		self.norm_tf = sum(math.pow(self.F_jc[k], 2) for k in self.n_jc.elements())
		self.N_c = float(self.article_count)

	def term_weighting(self, term):
		self.finalise()
		norm_F_jc = self.F_jc[term]/math.sqrt(self.norm_tf)
		pdf = math.pow(math.e, (self.n_jc[term]/self.N_c))
		return norm_F_jc * pdf

# Don't sublclass from newspaper.article as objects instantiated from
# this class must be serialisable with cPickle (...i.e. no lxml)
class Article:
	def __init__(self, article, id, publish_date, author, feed):
		self.id = id
		self.title = article.title
		self.text = article.text
		self.author = author
		self.html = article.article_html
		try:
			self.publish_date = publish_date.replace(tzinfo=pytz.UTC)
		except AttributeError as e:
			self.publish_date = publish_date

		self.summary = article.summary
		self.url = article.url
		self.img = article.top_image
		self.uuid = id
		self.feed_name = feed
		self.tokens, self.entities = tokenize(
			self.title +". "+ self.text,
			news_graph_knowledge
		)
		self.entities = list(set(self.entities).difference(self.author, self.feed_name))
		self.word_count = len(self.tokens)
		self.term_frequency = {}

	def termFrequency(self, term):
		if not self.term_frequency:
			for word in self.tokens + self.entities:
				current = self.term_frequency.get(word, 0)
				self.term_frequency[word] = current+1
		
		freq = self.term_frequency.get(term, 0)
		if freq == 0:
			return self.text.lower().count(term.lower())
		else: 
			return freq

	def containsTerm(self, term):
		return term.lower() in self.text.lower()


class NewsCollection:
	
	def __init__(self, feed_data):
		self.collection_by_id = {}
		self.collection_by_feed = {}
		self.article_count = len(feed_data)

		self.newsfeeds = {}
		for feed_name in set(f[2] for f in feed_data):
			feed = NewsFeed(feed_name)
			self.newsfeeds[feed_name] = feed
			self.collection_by_feed[feed] = []

		for (url, publish_date, feed_name, author) in tqdm(feed_data):
			article = RawArticle(url, keep_article_html=True)
			article.download()
			article.parse()
			article_id = uuid.uuid1()
			processed_article = Article(article, article_id, publish_date, author, feed_name)
			self.collection_by_id[article_id] = processed_article
			self.newsfeeds[feed_name].addArticle(processed_article)

		self.feed_count = len(self.collection_by_feed)

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

	def entity_tf_idf_vector(self, article_id, top_n=-1):
		vector = {}
		article = self.article(article_id)
		for i, term in enumerate(article.entities):
			tfidf = self.tf_idf(term, article_id)
			if tfidf:
				vector[term] = tfidf
		return dict(sorted(vector.iteritems(), key=operator.itemgetter(1), reverse=True)[:top_n])

	def tf_pdf(self, term):
		return sum(feed.term_weighting(term) for feed in self.newsfeeds.values())

	def top_article_keywords(self, top_n=10):
		ret = {}
		for id, article in self.collection_by_id.iteritems():
			for entity in self.entity_tf_idf_vector(id, top_n):
				update = ret.get(entity, [])
				update.append(article)
				ret[entity] = update
		return ret

	def top_corpus_keywords(self, top_n=25):
		ret = {}
		for entity in set(e for a in self.collection_by_id.values() for e in a.entities):
			update = ret.get(entity, [])
		 	ret[entity] = (self.tf_pdf(entity), [a for a in self.collection_by_id.values() if entity in a.entities])
		return dict((k, v[1]) for (k, v) in sorted(ret.iteritems(), key=operator.itemgetter(1), reverse=True)[:top_n])


read_cache = True	
write_cache = False

cln = None
if read_cache:
	rd = CacheReader()
	cln = rd.read()
else:
	feeds = ['http://www.independent.co.uk/news/uk/rss', 'https://www.theguardian.com/uk-news/rss']
	urls = []
	print "Fetching RSS Feed(s)"
	for feed in feeds:
		feed = feedparser.parse(feed)
		for item in feed["items"][:40]:
			urls.append(
				(item["link"], 
				item["published_parsed"], #Newspaper date extraction loses timestamps, which we want
				feed["channel"]["title"],
				item["author"])
			)
	cln = NewsCollection(urls)

if write_cache:
	wr = CacheWriter(strftime("%Y%m%d-%H%M%S")+".ng")
	wr.write(cln)

#TF-IDF
e_map = cln.top_article_keywords(6)
top_25 = sorted(e_map.iteritems(), key=lambda (k,a): len(a), reverse=True)[:15]

#TF-PDF
# top_25 = sorted(cln.top_corpus_keywords(5).iteritems(), key=lambda (k,a): len(a), reverse=True)

subsumed = {}
for pair1, pair2 in itertools.combinations(top_25, 2):
	kw1, articles1 = pair1[0], set(pair1[1])
	kw2, articles2 = pair2[0], set(pair2[1])
	unique = len(articles1.difference(articles2))/float(len(articles1))
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
	if len(articles) > 3:
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


