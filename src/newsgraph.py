import datetime
import feedparser
import newspaper
import operator

from itertools import combinations
from time import strftime

from newsUtils.newsfeeds import *
from ioUtils.newsSerialiser import *
from mapEngine.graphObjects import *

class Params:
  # Too many stations? Reduce this.
  RSS_LIMIT = 50

  # Stations too highly connected? Reduce this. (Vice versa for too sparse)
  TFIDF_VEC_LEN = 7 
  # Metro lines too vague? Increase this.
  CORPUS_KEYWORDS = 25 
  
  #Too many metro lines? Reduce this.
  METRO_LINES = 10 # 
  # Too few metro lines? Reduce this.
  MIN_LINE_LENGTH = 4 
  # Map empty due to too few common keywords? Invert this.
  TFIDF = True 
  TFPDF = not TFIDF

read_cache = True
read_cache_name = None # eg. old-cache.ng in the cwd

write_cache = False
write_cache_name = None # eg. my-cache.ng

feeds = [] # eg. ['https://www.theguardian.com/us-news/rss', ...]
interests = []
ignore = []

cln = None
if read_cache:
  rd = CacheReader(read_cache_name)
  cln = rd.read()
else:
  urls = []
  print "Fetching RSS Feed(s)"
  for feed in feeds:
    feed = feedparser.parse(feed)
    for item in feed["items"][:Params.RSS_LIMIT]:
      urls.append(
        (item["link"], 
        item["published_parsed"],
        feed["channel"]["title"],
        item.get("author", "")))
  cln = NewsCollection(urls)

if write_cache:
  wr = CacheWriter(write_cache_name)
  wr.write(cln)

top_keywords = None
if Params.TFIDF:
  e_map = cln.top_article_keywords(
    Params.TFIDF_VEC_LEN, include=interests, exclude=ignore)
  top_keywords = sorted(
    e_map.iteritems(), key=lambda (k,a): len(a), reverse=True
  )[:Params.CORPUS_KEYWORDS]
else: #tf-pdf
  top_keywords = sorted(
    cln.top_corpus_keywords(
      Params.CORPUS_KEYWORDS, include=interests, exclude=ignore
    ).iteritems(), key=lambda (k,a): len(a), reverse=True)

# Compute coverage for each keyword in the corpus
coverage = {}
for keyword, articles in top_keywords:
  for a in articles:
    if a in coverage: # This article is already on one or more lines
      coverage[a].append(keyword)
    else: # It's the first time we've seen this article
      coverage[a] = [keyword]

# Now coverage[article] will tell us which lines it is on,
# we penalise lines which cover already-covered articles.
value_added = dict((keyword, 0) for keyword,_ in top_keywords)
for keyword, articles in top_keywords:
  for a in articles:
    weight = len(coverage[a])
    value_added[keyword] += cln.tf_idf(keyword, a, id=False)/weight
  value_added[keyword] *= len(articles)

# Compute the affinity for each keyword
affinity = dict((keyword, 0) for keyword,_ in top_keywords)
for keyword, articles in top_keywords:
  line_affinity = dict((o, 0) for o,_ in top_keywords)
  del line_affinity[keyword] #Can't compute a line's affinity with itself
  for a in articles:
    others = [c for c in coverage[a] if c != keyword]
    for o in others:
      line_affinity[o] += 1
  for o, val in line_affinity.iteritems():
    line_affinity[o] = (2**val)
  affinity[keyword] = sum(line_affinity.values())/len(articles)

top_keywords = sorted(
  top_keywords, 
  key=lambda (e,a): value_added[e]/(max(1, affinity[e])), 
  reverse=True
)[:Params.METRO_LINES]

# Nodes and Links will be the two JSON objects passed to d3.
links = []
nodes = []

metro_lines = {}
node_lookup = {}
multiedge_counts = {}
stations = set()
termini = set()

for i, (e, articles) in enumerate(top_keywords):
  if len(articles) >= Params.MIN_LINE_LENGTH:
    ordered_line = sorted(articles, key=lambda a:a.publish_date)
    # Add the articles to node_lookup if they aren't already - this is a
    # simple 0 to (n-1) index of all n articles which will be in the graph.
    # Also, update the lines passing through station a to include this one.
    for n, a in enumerate(ordered_line):
      node_lookup[a] = node_lookup.get(a, len(node_lookup.keys()))
      a.metro_lines.append(e)
      stations.add(a)

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

for a,i in sorted(node_lookup.iteritems(), key=lambda x:x[1]):
  nodes.append({"name": a.title, "lines":a.metro_lines, "data":a.data()})
for i, node in enumerate(nodes):
  node["terminus"] = (i in termini)

# Generate the graph
ng = NewsGraph(nodes, links, stations, metro_lines, node_lookup)