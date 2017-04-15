import datetime
import math
import newspaper
import operator
import pytz
import string
import uuid

from collections import Counter
from newspaper import Article as RawArticle
from time import mktime
from tqdm import tqdm

from keywordUtils.corpusUtilities import *

class NewsFeed:
  """
  Container class for instances of Article; used to calculate tf-pdf metrics.
  """
  def __init__(self, feed_name):
    """
    Initialise NewsFeed from a single RSS feed.
    """
    self.name = feed_name
    self.F_jc = Counter()  # Frequency of term within articles in this feed
    self.n_jc = Counter()  # Articles in the feed which contain this term
    self.article_count = 0 # Total articles in the feed

  def addArticle(self, article):
    """
    Add a new article to the feed and update the tf-pdf metrics.
    """
    self.finalised = False
    self.article_count += 1
    for e in article.entities:
      self.n_jc[e] += 1
      self.F_jc[e] += article.termFrequency(e)

  def finalise(self):
    """
    Finalise the feed for tf-pdf calculations. 
    This must be called again if any new articles are added.
    """
    self.finalised = True
    self.norm_tf = sum(self.F_jc[k]**2 for k in self.n_jc.elements())
    self.N_c = float(self.article_count)

  def term_weighting(self, term):
    """Calculate the term weighting metric for tf-pdf in this channel."""
    if not self.finalised:
      self.finalise()
    norm_F_jc = self.F_jc[term]/math.sqrt(self.norm_tf)
    pdf = math.pow(math.e, (self.n_jc[term]/self.N_c))
    return norm_F_jc * pdf

# Don't sublclass from newspaper.article as objects instantiated from
# this class must be serialisable to the cache using cPickle (i.e. no lxml)
class Article:
  """
  Serialisable wrapper around Newspaper.Article, with meta from Goose.
  """
  def __init__(self, article, id, publish_date, author, feed):
    """
    Create a new instance of Article from params. This will perform
    text & date parsing, tokenisation and entity disambiguation.
    """
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
    self.tokens, self.entities, self._ent_frequency = tokenize(
      ".".join(self.title, self.text))
    self.entities = list(
      set(self.entities).difference(self.author, *self.feed_name.split()))
    self.word_count = len(self.tokens)
    self.term_frequency = {}
    try:
      self.publish_date = publish_date.replace(tzinfo=pytz.UTC)
    except AttributeError as e:
      self.publish_date = publish_date

  def termFrequency(self, term):
    """
    Calculate the tf of {term} in this article
    """
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
    """
    Boolean check of {term} in article
    """
    return term.lower() in self.text.lower() or self._ent_frequency[term]

  def data(self):
    """
    Return a JSON object containing the pane data for this article/station 
    """
    html = (self.summary + "<br/><br/><a href='%s'>Read more at %s</a>" % 
      (self.url, self.feed_name))
    return {
      "title": self.title,
      "date": 1000*mktime(self.publish_date),
      "summary": self.summary,
      "img": self.img,
      "url": self.url,
      "html": html
    }

class NewsCollection:
  """
  Container class for instances of NewsFeed. Used for corpus-wide metrics.
  """
  def __init__(self, feed_data):
    """
    Create a new instance of NewsCollection-(1:m)-NewsFeed-(1:m)-Article
    """
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
      processed_article = Article(
        article, article_id, 
        publish_date, author, feed_name)
      self.collection_by_id[article_id] = processed_article
      self.newsfeeds[feed_name].addArticle(processed_article)

    self.feed_count = len(self.collection_by_feed)

  def article(self, article_id):
    """
    Get the article object by its id.
    """
    return self.collection_by_id.get(article_id, None)

  def idf(self, term):
    """
    Calculate the inverse document frequency for {term} in this corpus.
    """
    n_containing = 0
    for article in self.collection_by_id.values():
      if article.containsTerm(term):
        n_containing += 1
    return math.log(self.article_count/n_containing)

  def tf_idf(self, term, article, id=True):
    """
    Calculate the tf-idf for {term} in {article} in this corpus.
    {article} can either be by val or by id.
    """
    if id:
      article = self.article(article)
    try:
      return article.termFrequency(term) * self.idf(term)
    except ZeroDivisionError:
      pass # Probably a whitespace/punctuation error
      #raise KeyError('Keyword "%s" does not exist in any article' % term)

  def entity_tf_idf_vector(self, article_id, top_n=-1, include=[], boost=10):
    """
    Return the top n entities in this article by descending tf-idf.
    Default n = all.
    Boost the score of any terms in {include} by {boost, default=10}
    """
    vector = {}
    article = self.article(article_id)
    for i, term in enumerate(article.entities):
      tfidf = self.tf_idf(term, article_id)
      if tfidf:
        vector[term] = tfidf
        if term in include:
          vector[term] *= boost
    return dict(sorted(
        vector.iteritems(), key=operator.itemgetter(1), reverse=True
      )[:top_n])

  def tf_pdf(self, term):
    """
    Calculate the tf-pdf of {term} in this corpus
    """
    return sum(feed.term_weighting(term) for feed in self.newsfeeds.values())

  def top_article_keywords(self, top_n=10, include=[], exclude=[]):
    """
    Return a dictionary of {entities:containing articles} in this Article
    """
    ret = {}
    for id, article in self.collection_by_id.iteritems():
      for entity in self.entity_tf_idf_vector(id, top_n, include):
        if entity not in exclude:
          update = ret.get(entity, [])
          update.append(article)
          ret[entity] = update
    return ret

  def top_corpus_keywords(self, top_n=25, include=[], exclude=[], boost=10):
    """
    Return a dictionary of the top {entity:[(score,article),...]} in this 
    corpus, with words in {include} boosted and words in {exclude} ignored.
    """
    ret = {}
    corpus_entities = set(
      e for a in self.collection_by_id.values() for e in a.entities 
      if e not in exclude)

    for entity in corpus_entities:
      update = ret.get(entity, [])
      tfpdf = self.tf_pdf(entity)
      if entity in include:
        tfpdf *= boost
      ret[entity] = (tfpdf, 
        [a for a in self.collection_by_id.values() 
        if entity in a.entities])

    return dict((k, v[1]) for (k, v) in sorted(
      ret.iteritems(), key=operator.itemgetter(1), reverse=True)[:top_n])