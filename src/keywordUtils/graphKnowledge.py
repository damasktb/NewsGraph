import json
import urllib

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
				desc = response['result']['detailedDescription'][u'articleBody'].encode('utf-8')
			self.candidates.append((
				response['result'].get('name', query),
				response['result']['@type'],
				desc,
				response['resultScore'],
			))
		if len(candidates) == 0:
			self.certainty = 0
		elif len(candidates) == 1:
			self.certainty = maxint
		else:
			self.certainty = candidates[0]['resultScore']/candidates[1]['resultScore']
	
	def nth(self, n):
		if self.candidates and len(self.candidates) > n-1:
			return self.candidates[n-1]
		else:
			return None

	def top(self):
		return self.nth(1)

	def isPerson(self):
		return "Person" in self.candidates[0][NewsGraphResult.TYPES] if self.candidates else None


class NewsGraphKnowledge:
	LOG = False
	default_api_key = 'keywordUtils/.api_key'

	def __init__(self):
		self.api_key = open(NewsGraphKnowledge.default_api_key).read()
		self.service_url = 'https://kgsearch.googleapis.com/v1/entities:search'

	def query(self, queryText, limit=4):
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
		if 'itemListElement' in response:
			return NewsGraphResult(queryText, response['itemListElement'])
		else:
			return None

	def aliasEntities(self, entities, certainty=2):
		uncertain = []
		mapping = {}
		people = {}

		entities.sort(key=lambda e:len(e), reverse=True)

		popular_entities = list(set([e for e in entities if entities.count(e) > 1]))
		entities = list(set(entities))

		#print entities
		for queryText in entities:
			# early_match = False
			# for e in entities:
			# 	if queryText == e and queryText is not e:
			# 		mapping[queryText] = queryText
			# 		early_match = True
			# 		break
			# 	if queryText in e and queryText is not e:
			# 		if queryText in mapping: #multiple matches
			# 			print queryText, "matched with both", mapping[queryText], "and", e
			# 			del mapping[queryText]
			# 			early_match = False
			# 		else:
			# 			if e in mapping:
			# 				mapping[queryText] = mapping[e]
			# 				early_match = True

			# if early_match:
			# 	continue

			result = self.query(queryText)
			if result == None:
				continue
				
			if result.certainty > certainty or e in popular_entities:
				if NewsGraphKnowledge.LOG:
					print "Certain: %s => %s (%s)" % (
						queryText, 
						result.top()[NewsGraphResult.NAME],
						result.top()[NewsGraphResult.DESCR]
					)
				name = result.top()[NewsGraphResult.NAME]
				if name in people:
					mapping[queryText] = people[name]
				else:
					mapping[queryText] = name
					if result.isPerson() and " " in name:
						for word in name.split(" "):
							if word in people and people[word] != name:
								if NewsGraphKnowledge.LOG:
									print "Ambigiuty, can't alias", word, "to both", name,  "and", names[word]
								del people[word]
							else:
								people[word] = name
			else:
				if queryText in people:
					mapping[queryText] = people[queryText]
				else:
					for n in range(2, 4):
						candidate = result.nth(n)
						if candidate and candidate[NewsGraphResult.NAME] in mapping:
							if NewsGraphKnowledge.LOG:
									print "Matching", queryText, "to", candidate[NewsGraphResult.NAME]
							queryText = candidate[NewsGraphResult.NAME]
							break
					mapping[queryText] = queryText

		return dict((entity, alias) for entity, alias in mapping.iteritems() if entity!=alias)