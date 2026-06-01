class Selection:
	def __init__(self):
		self.active = False

		self.startX = 0
		self.startY = 0

		self.endX = 0
		self.endY = 0

	def clear(self):
		self.active = False
	
	def begin(self, x, y):
		self.active = True

		self.startX = x
		self.startY = y

		self.endX = x
		self.endY = y

	def update(self, x, y):
		if not self.active:
			return
		self.endX = x
		self.endY = y

	def normalized(self):
		start = (self.startY, self.startX)
		end = (self.endY, self.endX)

		if start > end:
			start, end = end, start
		
		return start, end

	def contains(self, x, y):
		if not self.active:
			return False
		(sx, sy), (ex, ey) = self.normalized()
		
		if y < sy or y > ey:
			return False
		if sy == ey:
			return sx <= x < ex
		if y == sy:
			return x >= sx
		if y == ey:
			return x < ex
		return True

	def selectedColumns(self, lineY):
		if not self.active:
			return None
		(sx, sy), (ex, ey) = self.normalized()

		if lineY < sy or lineY > ey:
			return None
		if sy == ey:
			return (sx, ex)
		if lineY == sy:
			return (sx, None)
		if lineY == ey:
			return (0, ex)
		return (0, None)