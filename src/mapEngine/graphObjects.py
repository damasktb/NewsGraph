from webUtils.html import writePage

class NewsGraph:
	def __init__(self, nodes, links, articles, lines, indexes):
		writePage(nodes, links, articles, lines)