import datetime
import feedparser
import math
import newspaper
import operator
import planarity
import pytz
import string
import sys
import uuid

from collections import defaultdict, Counter
from itertools import combinations
from newspaper import Article as RawArticle
from time import mktime, strftime
from tqdm import tqdm

from ioUtils.newsSerialiser import *
from keywordUtils.corpusUtilities import *
from mapEngine.graphObjects import *

class NewsFeed:
	def __init__(self, feed_name):
		self.name = feed_name
		self.F_jc = Counter() # Frequency of all terms in the channel
		self.n_jc = Counter() # Number of documents in the channel which contain the term
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
		self.author = author
		self.html = article.article_html
		self.text, self.summary = parseHTML(article)
		self.img = article.top_img
		self.url = article.url
		self.feed_name = feed
		self.metro_lines = []
		self.line_idx = {}
		self.tokens, self.entities, self._ent_frequency = tokenize(self.title +". "+ self.text)
		self.entities = list(set(self.entities).difference(self.author, *self.feed_name.split()))
		self.word_count = len(self.tokens)
		self.term_frequency = {}
		try:
			self.publish_date = publish_date.replace(tzinfo=pytz.UTC)
		except AttributeError as e:
			self.publish_date = publish_date

	def retokenize(self):
		self.tokens, self.entities, self._ent_frequency = tokenize(self.title +". "+ self.text)

	def termFrequency(self, term):
		if self._ent_frequency[term]:
			return self._ent_frequency[term]

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
		return (term.lower() in self.text.lower()) or (self._ent_frequency[term])

	def data(self):
		html = self.summary + "<br/><br/><a href='%s'>Read more at %s</a>" % (self.url, self.feed_name)
		return {
			"title": self.title,
			"date": 1000*mktime(self.publish_date),
			"summary": self.summary,
			"img": self.img,
			"url": self.url,
			"html": html
		}

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

	def retokenize(self):
		for a in self.collection_by_id.values():
			a.retokenize()

	def article(self, article_id):
		return self.collection_by_id.get(article_id, None)

	def idf(self, term):
		n_containing = 0
		for article in self.collection_by_id.values():
			if article.containsTerm(term):
				n_containing += 1
		return math.log(self.article_count/n_containing)

	def tf_idf(self, term, article, id=True):
		if id:
			article = self.article(article)
		try:
			return article.termFrequency(term) * self.idf(term)
		except ZeroDivisionError:
			pass
			#Probably a whitespace/punctuation error
			#raise KeyError('Keyword "%s" does not exist in any article' % term)

	def entity_tf_idf_vector(self, article_id, top_n=-1, include=[]):
		vector = {}
		article = self.article(article_id)
		for i, term in enumerate(article.entities):
			tfidf = self.tf_idf(term, article_id)
			if tfidf:
				vector[term] = tfidf
				if term in include:
					vector[term] *= 100
		return dict(sorted(vector.iteritems(), key=operator.itemgetter(1), reverse=True)[:top_n])

	def tf_pdf(self, term):
		return sum(feed.term_weighting(term) for feed in self.newsfeeds.values())

	def top_article_keywords(self, top_n=10, include=[], exclude=[]):
		ret = {}
		for id, article in self.collection_by_id.iteritems():
			for entity in self.entity_tf_idf_vector(id, top_n, include):
				if entity not in exclude:
					update = ret.get(entity, [])
					update.append(article)
					ret[entity] = update
		return ret

	def top_corpus_keywords(self, top_n=25, include=[], exclude=[]):
		ret = {}
		for entity in set(e for a in self.collection_by_id.values() for e in a.entities if e not in exclude):
			update = ret.get(entity, [])
			tfpdf = self.tf_pdf(entity)
			if entity in include:
				tfpdf *= 100
		 	ret[entity] = (tfpdf, [a for a in self.collection_by_id.values() if entity in a.entities])
		return dict((k, v[1]) for (k, v) in sorted(ret.iteritems(), key=operator.itemgetter(1), reverse=True)[:top_n])


read_cache = True
write_cache = False
interests = ["Education", "Institute for Fiscal Studies"]
ignore = ["Getty", "Getty Images", "READ MORE", "Read More","Video","Guardian", "European", "English", "London", "British", "Scottish", "Scotland", "House", "Commons", "Britain"]

cln = None
if read_cache:
	rd = CacheReader('guardian-us.ng')
	cln = rd.read()
	# cln.retokenize()
else:
	# feeds = ['http://independent.co.uk/news/uk/rss'
	# 		,'http://feeds.bbci.co.uk/news/uk/rss.xml'
	# 		,'https://www.theguardian.com/uk-news/rss']
	feeds = ['https://www.theguardian.com/us-news/rss']
	urls = []
	print "Fetching RSS Feed(s)"
	for feed in feeds:
		feed = feedparser.parse(feed)
		for item in feed["items"][:60]:
			urls.append(
				(item["link"], 
				item["published_parsed"], #Newspaper date extraction loses timestamps, which we want
				feed["channel"]["title"],
				item.get("author", ""))
			)
	cln = NewsCollection(urls)

if write_cache:
	#"news-"+strftime("%Y%m%d-%H%M%S")+".ng"
	wr = CacheWriter('guardian-us.ng')
	wr.write(cln)

# #TF-IDF
e_map = cln.top_article_keywords(7, include=interests, exclude=ignore)
top_25 = sorted(e_map.iteritems(), key=lambda (k,a): len(a), reverse=True)[:20]

#TF-PDF 
#top_25 = sorted(cln.top_corpus_keywords(25, include=interests, exclude=ignore).iteritems(), key=lambda (k,a): len(a), reverse=True)

coverage = {}
for e, arts in top_25:
	for a in arts:
		if a in coverage: # This article is already on one or more lines
			coverage[a].append(e)
		else: # First time we've seen this article
			coverage[a] = [e] #not yet seen

# now coverage[article] will tell us which lines it is on
# - we penalise lines which cover already-covered articles
value_added = dict((e, 0) for e,_ in top_25)
for e, arts in top_25:
	for a in arts:
		if "not the time" in a.title:
			print a.title, a.id, a.entities
			print "\n"
			print cln.entity_tf_idf_vector(a.id, top_n=1)
			print "\n"
		weight = len(coverage[a]) # 1 <= coverage[a] <= len(top_25)
		value_added[e] += cln.tf_idf(e, a, id=False)/weight
	value_added[e] *= len(arts)

affinity = dict((e, 0) for e,_ in top_25)
for e, arts in top_25:
	line_affinity = dict((o, 0) for o,_ in top_25)
	del line_affinity[e] # Can't do a line's affinity with itself
	for a in arts:
		others = [c for c in coverage[a] if c != e]
		for o in others:
			line_affinity[o] += 1
	for o, val in line_affinity.iteritems():
		line_affinity[o] = (2**val)
	affinity[e] = sum(line_affinity.values())/len(arts)


print "\n"
top_25 = sorted(top_25, key=lambda (e,a):value_added[e], reverse=True)
for e, a in top_25:
	print e, ": value added = ", str(value_added[e]), "affinity = ", str(affinity[e])
print "\n"

top_25 = sorted(top_25, key=lambda (e,a):value_added[e]/(max(1, affinity[e])), reverse=True)[:10]

subsumed = {}
for pair1, pair2 in combinations(top_25, 2):
	kw1, articles1 = pair1[0], set(pair1[1])
	kw2, articles2 = pair2[0], set(pair2[1])
	unique = len(articles1.difference(articles2))/float(len(articles1))
	if unique < 0.5 and kw1 not in interests:
		print kw1, " maybe subsumed by ", kw2
		if unique < 0.2:
			subsumed[kw1] = kw2

new_top = {}
for (k, articles) in top_25:
	while k in subsumed:
		print k, " subsumed by ", subsumed[k]
		k = subsumed[k]
	
	arts_for_keyword = new_top.get(k, set())
	arts_for_keyword.update(articles)
	new_top[k] = arts_for_keyword

links = []
nodes = []
metro_lines = {}
node_lookup = {}
multiedge_counts = {}
arts = set()
termini = set()

for i, (e, articles) in enumerate(new_top.iteritems()):
	# We're only interested in lines of a reasonable length 
	if len(articles) > 2:
		ordered_line = sorted(articles, key=lambda a:a.publish_date)
		print e
		for a in ordered_line:
			print "-", a.title

		# Add the articles to node_lookup if they aren't already - this is a simple
		# 0 to (n-1) index of all n articles which will be in the graph.
		# Also, update the lines passing through station a to include this one.
		for n, a in enumerate(ordered_line):
			node_lookup[a] = node_lookup.get(a, len(node_lookup.keys()))
			a.metro_lines.append(e)
			arts.add(a)

		metro_lines[e] = []
		termini.add(node_lookup[ordered_line[0]])
		termini.add(node_lookup[ordered_line[-1]])
		for n in range(len(ordered_line)-1):
			source = node_lookup[ordered_line[n]]
			target = node_lookup[ordered_line[n+1]]
			count = multiedge_counts.get((source, target), 0)+1
			multiedge_counts[(source, target)] = count
			
			links.append({
				"source": source,
				"target": target,
				"count": count,
				"line": e,
			})
			metro_lines[e].append((source, target))

nodes = []
for a,i in sorted(node_lookup.iteritems(), key=lambda x:x[1]):
	nodes.append({"name": a.title, "lines":a.metro_lines, "data":a.data()})
for i, node in enumerate(nodes):
	node["terminus"] = (i in termini)
ng = NewsGraph(nodes, links, arts, metro_lines, node_lookup)



