import json
import urllib

from collections import Counter

from itertools import combinations
from sys import maxint

class NewsGraphResult:
	NAME  = 0
	TYPES = 1
	DESCR = 2
	SCORE = 3

	def __init__(self, query, candidates):
		self.query = query
		self.candidates = []
		for response in candidates: 
			desc = response['result'].get('description', "")
			if 'detailedDescription' in response['result']:
				desc = response['result']['detailedDescription']
				desc = desc[u'articleBody'].encode('utf-8')
			self.candidates.append((
				response['result'].get('name', query),
				response['result']['@type'],
				desc,
				response['resultScore'],
			))
		if len(candidates) < 2:
			self.certainty = 0
		else:
			first = candidates[0]['resultScore']
			second = candidates[1]['resultScore']
			self.certainty = first/second
				
	
	def nth(self, n):
		if self.candidates and len(self.candidates) > n-1:
			return self.candidates[n-1]
		else:
			return None

	def top(self):
		return self.nth(1)

	def isPerson(self):
		if self.candidates:
			return "Person" in self.candidates[0][NewsGraphResult.TYPES]
		return None


class NewsGraphKnowledge:
	LOG = False
	IGNORE = [u"AP", u"Caption", u"Getty Images Image", u"Getty Images", 
			u"Getty", u"Photograph", u"Photo", u"Facebook Twitter Pinterest"]
	API_KEY = 'keywordUtils/.api_key'

	def __init__(self):
		self.api_key = open(NewsGraphKnowledge.API_KEY).read()
		self.service_url = 'https://kgsearch.googleapis.com/v1/entities:search'

	def query(self, queryText, limit=3):
		params = {
			'query': queryText,
			'limit': limit,
			'indent': True,
			'key': self.api_key,
		}
		url = self.service_url + '?' + urllib.urlencode(params)
		response = json.loads(urllib.urlopen(url).read())

		if 'itemListElement' in response:
			return NewsGraphResult(queryText, response['itemListElement'])
		else:
			return None

	def popular(popular_entities, result):
		return result.top()[NewsGraphResult.NAME] in popular_entities

	def aliasEntities(self, entities, certainty=3):
		uncertain = []
		mapping = {}
		people = {}

		strength = {e: entities.count(e) for e in entities}

		popular_entities = list(set(
			[e for e in entities 
			if entities.count(e) > 2 and len(e) 
			and e not in NewsGraphKnowledge.IGNORE]
		))

		out = set()
		for e1, e2 in combinations(popular_entities, 2):
			if len(e1) > len(e2):
				tmp = e1
				e1 = e2
				e2 = tmp
			if e1 in e2:
				if e1 in mapping:
					del mapping[e1]
					out.remove(e1)
				else:
					mapping[e1] = e2
					out.add(e1)

		popular_entities = [e for e in popular_entities if e not in out]

		entity_set = list(set(entities))
		entity_set.sort(key=lambda e:len(e), reverse=True)

		for queryText in entity_set:
			if isinstance(queryText, unicode):
				queryText = queryText.encode('utf-8')
			elif isinstance(queryText, str):
				queryText.decode('utf-8')
			result = self.query(queryText)

			if result==None or result.top()==None:
				continue

			if result.certainty > certainty or popular(popular_entities, result):
				if NewsGraphKnowledge.LOG:
					n = result.top()[NewsGraphResult.NAME]
					if isinstance(n, unicode):
						n = n.encode('utf-8')
					elif isinstance(n, str):
						n.decode('utf-8')
					print "Certain: %s => %s" % (queryText, n)
				
				name = result.top()[NewsGraphResult.NAME]
				if name in people:
					mapping[queryText] = people[name]
				else:
					mapping[queryText] = name
					if result.isPerson() and " " in name:
						for word in name.split(" "):
							if word in people and people[word] != name:
								if NewsGraphKnowledge.LOG:
									print "Ambigiuty, ignoring", name
							else:
								people[word] = name
			else:
				if queryText in people:
					mapping[queryText] = people[queryText]
				else:
					mapping[queryText] = queryText

		aliases = dict(
			(entity, alias) for entity, alias in mapping.iteritems() 
			if entity!=alias
		)
		freqs = Counter([aliases.get(e, e) for e in entities])
		return aliases, freqs