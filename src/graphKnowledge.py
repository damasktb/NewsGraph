import json
import urllib

import itertools

from sys import maxint
from stop_words import get_stop_words
from unidecode import unidecode

class NewsGraphResult:
	NAME  = 0
	TYPES = 1
	DESCR = 2
	SCORE = 3

	def __init__(self, query, candidates):
		self.query = query
		self.candidates = []
		for response in candidates:
			self.candidates.append((
				response['result'].get('name', query),
				response['result']['@type'],
				response['result'].get('description', response['result'].get('name', query)),
				response['resultScore'],
			))
		if len(candidates) == 0:
			self.certainty = 0
		elif len(candidates) == 1:
			self.certainty = 2
		else:
			self.certainty = candidates[0]['resultScore']/candidates[1]['resultScore']

	def top(self):
		return self.candidates[0] if self.candidates else None


class NewsGraphKnowledge:
	LOG = True

	def __init__(self):
		self.api_key = open('.api_key').read()
		self.service_url = 'https://kgsearch.googleapis.com/v1/entities:search'

	def query(self, queryText, limit=3):
		if isinstance(queryText, unicode):
			queryText = queryText.encode('utf-8')
		elif isinstance(queryText, str):
			queryText.decode('utf-8')
		params = {
			'query': queryText,
			'limit': limit,
			'indent': True,
			'key': self.api_key,
		}
		url = self.service_url + '?' + urllib.urlencode(params)
		response = json.loads(urllib.urlopen(url).read().decode('utf-8'))
		return NewsGraphResult(queryText, response['itemListElement'])

	def aliasEntities(self, entities, certainty=2):
		domain = set()
		uncertain = []
		mapping = {}
		'''
		First Pass:
		Create a domain based on the keywords of the descriptions of every
		entity which we have identified above the certainty threshold.
		'''
		entities.sort(key=lambda e:len(e))
		for e, other in itertools.combinations(entities, 2):
			if e in other and e not in mapping:
				mapping[e] = other

		for queryText in entities:
			if queryText in mapping:
				print "skipping", queryText
				continue
			early_match = False
			for entity in mapping.keys():
				if queryText in entity:
					mapping[queryText] = mapping[entity]
					if NewsGraphKnowledge.LOG:
						print "Assuming: %s => %s" % (
							queryText, 
							mapping[queryText]
						)
					early_match = True
					break
			if early_match:
				continue

			result = self.query(queryText)
			if result.certainty > certainty and result.top()[NewsGraphResult.SCORE] > 100:
				if NewsGraphKnowledge.LOG:			
					print "Certain: %s => %s (%s)" % (
						queryText, 
						result.top()[NewsGraphResult.NAME],
						result.top()[NewsGraphResult.DESCR]
					)
				mapping[queryText] = result.top()[NewsGraphResult.NAME]
				for keyword in result.top()[NewsGraphResult.NAME]:
					domain.add(keyword)
			else: 
				uncertain.append(result)
		domain = domain.difference(set(get_stop_words("en")))
		'''
		Second Pass:
		For every unmatched entity, choose the candidate which shares the highest
		percentage of the words in its name with the domain. If this is <50%,
		consider the entity unmatched.
		'''
		for result in uncertain:
			highest = (0, None)
			for keyword in domain:
				keyword = keyword.encode('utf-8')
				if result.query in keyword:
					mapping[result.query] = keyword
					print "Exact match %s => %s" % (
						word, 
						result.query, 
					)
					early_match = True
					break
			if early_match:
				continue

			for c in result.candidates:
				# What percentage of words in this description are 
				# in descriptions for other entities in the document?
				words = set(c[NewsGraphResult.NAME].split())
				words = words.difference(set(get_stop_words("en")))
				match = 100.0*sum([1 for w in words if w in domain])/len(words)
				if match > highest[0]:
					highest = (match, c)
			if highest[1] and highest[0] > 50:
				if NewsGraphKnowledge.LOG:
					print "%d%% match %s => %s (%s)" % (
						highest[0], 
						result.query, 
						highest[1][NewsGraphResult.NAME],
						str(highest[1][NewsGraphResult.DESCR])
					)
				mapping[result.query] = highest[1][NewsGraphResult.NAME]
			# else:
			# 	print "Unmatched:", result.query
		return dict((entity, alias) for entity, alias in mapping.iteritems() if entity!=alias)




