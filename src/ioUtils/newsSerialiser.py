try:
	import cPickle as pickle
except:
	import pickle

class Cache:
	DEFAULT = "io_ignore/cache.ng"
	def __init__(self, file_name=DEFAULT):
		self.fname = file_name

class CacheWriter(Cache):
	def write(self, cln):
		with open(self.fname, 'wb') as cache:
			pickle.dump(cln, cache)

class CacheReader(Cache):  	
  	def read(self):
  		cln = None
		with open(self.fname, 'rb') as cache:
  			cln = pickle.load(cache)		
  		return cln