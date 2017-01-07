import math

from random import randint, choice
from webUtils.html import writePage
from sys import maxint

class NewsGraph:
	def __init__(self, nodes, links, articles, lines, indexes):
		writePage(nodes, links, articles, lines)

class Criteria:
	def __init__(self):
		self.edgeCrossingC = maxint
		self.octilinearityC = maxint
		self.lineStraightC = 0
		# self.angularResC = maxint
		# self.edgeLengthC = maxint
		# self.balancedEdgeC = maxint

	def linelength(self, x1, y1, x2, y2):
		return math.sqrt((x1-x2)**2 + (y1-y2)**2)

	def lineStraightness(self, line_coords):
		# Need line_coords to be a list of pairs of (x,y)
		ls = 0
		for line in line_coords:
			for i in range(len(line)-3):
				# Calculate the smallest angle between edges ab and bc
				(ax, ay), (bx, by), (cx, cy) = line[i], line[i+1], line[i+2]
				r = self.linelength(ax, ay, bx, by)
				p = self.linelength(ax, ay, cx, cy)
				r_term = 2*(r**2)
				ls += math.pi - math.acos((r_term-p**2)/float(r_term))
		return ls

	def octilinearity(self, line_coords):
		# Need line_coords to be a list of pairs of (x,y)
		ol = 0
		for line in line_coords:
			for i in range(len(line)-2):
				# Calculate the gradient of edge ab 
				# (penalise if not a multiple of 45 deg)
				(ax, ay), (bx, by) = line[i], line[i+1]
				opp = math.abs(ay-by)
				adj = math.abs(ax-bx)
				grad = 4 * math.atan(opp/float(adj))
				ol += math.abs(math.sin(grad))
		return ol





class MapGrid:
	DIRS = ["E", "SE", "S", "SW", "W", "NW", "N", "NE"] 

	def __init__(self, articles, lines, indexes, longestline):
		self.d = 2*longestline
		self.lines = sorted(lines, key=lambda x:len(x[1]), reverse=True)
		self.articles = articles
		self.id = indexes
		self.grid = [[0 for x in xrange(self.d)] for x in xrange(self.d)]
		self.tmp_grid = [[0 for x in xrange(self.d)] for x in xrange(self.d)]

	def random_direction(self):
		return choice(MapGrid.DIRS)

	def closest_directions(self, current):
		ret = [current]
		d = MapGrid.DIRS.index(current)
		close = [d-1, d-2, d+1, d+2]
		for d in close:
			d = d%len(MapGrid.DIRS)
			ret.append(MapGrid.DIRS[d])
		return ret

	def position_nodes(self, nodes):
		placed = {}
		next

		# (line, articles) = self.lines[0]
		# for i, article in enumerate(line):
		# 	placed[article.id] = (self.d/2, i)
		# 	self.grid[self.d/2][i] = article

		# curr_r, curr_c = self.random_cell()
		# curr_d = "E"
		# for (line, articles) in self.lines[1:]:
		# 	for i, article in enumerate(articles):
		# 		if article.id not in placed:
		# 			for d in self.closest_directions(curr_d):
		# 				if self.can_move(curr_r, curr_c, d):
		# 					curr_d = d
		# 					curr_r, curr_c = self.move(curr_r, curr_c, curr_d)
		# 					self.grid[curr_r][curr_c] = article
		# 					placed[article.id] = (curr_r, curr_c)
		# 					break

		# for r, row in enumerate(self.grid):
		# 	for c, cell in enumerate(row):
		# 		if cell != 0:
		# 			nodes[self.id[cell]]["x"]  = c
		# 			nodes[self.id[cell]]["px"] = c
		# 			nodes[self.id[cell]]["y"]  = r
		# 			nodes[self.id[cell]]["py"] = r
		# 			nodes[self.id[cell]]["fixed"] = True
		return nodes

	def move(self, r, c, direction):
		if "N" in direction:
			r -= 1
		if "E" in direction:
			c += 1
		if "S" in direction:
			r += 1
		if "W" in direction:
			c -= 1
		return r, c

	def can_move(self, r, c, direction):
		if "N" in direction:
			r -= 1
		if "E" in direction:
			c += 1
		if "S" in direction:
			r += 1
		if "W" in direction:
			c -= 1
		if (r > 0 and r < self.d and c > 0 and c < self.d):
			return (self.grid[r][c] == 0)
		else:
			return False

	def random_cell(self, r=0, c=0):
		while self.grid[r][c] != 0 or self.grid[r][c-1] != 0 or self.grid[r][c+1] != 0:
			r = randint(0, self.d-1)
			c = randint(0, self.d-1)
		return r, c

	def print_grid(self):
		for row in self.grid:
			for cell in row:
				if cell == 0:
					cell = "."
				else:
					cell = str(self.id[cell])
				print cell.ljust(3),
			print ""



