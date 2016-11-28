import time
try:
	import cPickle as pickle
except:
	import pickle


DEFAULT = "cache.ng"

class CacheWriter:

	def __init__(self, file_name=DEFAULT):
		self.fname = file_name

	def write(self, cln):
		with open(self.fname, 'wb') as cache:
			pickle.dump(cln, cache)

class CacheReader:
	
	def __init__(self, file_name=DEFAULT):
		self.fname = file_name
  	
  	def read(self):
  		cln = None
		with open(self.fname, 'rb') as cache:
  			cln = pickle.load(cache)		
  		return cln