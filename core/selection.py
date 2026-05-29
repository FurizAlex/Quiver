class Selection:
	def __init__(self):
		self.active = False

		self.startX = 0
		self.startY = 0

		self.endX = 0
		self.endY = 0
	
	def begin(self, x, y):
		self.active = True

		self.startX = x
		self.startY = y

		self.endX = x
		self.endY = y

	def update(self, x, y):
		self.endX = x
		self.endY = y

	def clear(self):
		self.active = False

	def normalized(self):
		start = (self.startY, self.startX)
		end = (self.endY, self.endX)

		if start > end:
			start, end = end, start
		
		return (start[1], start[0], end[1], end[0])

	def contains(self, x, y):
		if not self.active:
			return False
		sx, sy, ex, ey = self.normalized()
		
		if y < sy or y > ey:
			return False
		if sy == ey:
			return sx <= x < ex
		if y == sy:
			return x >= sx
		if y == ey:
			return x < ex
		return True