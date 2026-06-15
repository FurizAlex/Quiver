class MultiSelection:
	def __init__(self):
		self.selections = []
		self.active = False

	def begin(self, x, y):
		self.selections = []
		self.active = True
		self.selections.append([x, y, x, y])

	def update(self, x, y):
		if self.selections:
			self.selections[-1][2] = x
			self.selections[-1][3] = y

	def addSelection(self, sx, sy, ex, ey):
		self.selections.append([sx, sy, ex, ey])

	def clear(self):
		self.selections = []
		self.active = False

	def normalized(self):
		if not self.selections:
			return {"sx": 0, "sy": 0, "ex": 0, "ey": 0}
		s = self.selections[-1]
		if (s[1], s[0]) <= (s[3], s[2]):
			return {"sx": s[0], "sy": s[1], "ex": s[2], "ey": s[3]}
		return {"sx": s[2], "sy": s[3], "ex": s[0], "ey": s[1]}
	
	def allNormalized(self):
		result = []
		for s in self.selections:
			if (s[1], s[0]) <= (s[3], s[2]):
				result.append({"sx": s[0], "sy": s[1], "ex": s[2], "ey": s[3]})
			else:
				result.append({"sx": s[2], "sy": s[3], "ex": s[0], "ey": s[1]})
		return result
	
	def contains(self, x, y):
		for select in self.allNormalized():
			if self.inRange(x, y, select):
				return True
		return False
	
	def selectedColumns(self, y):
		for select in self.allNormalized():
			if select["sy"] <= y <= select["ey"]:
				sc = select["sx"] if y == select["sy"] else None
				ec = select["ex"] if y == select["ey"] else None
				return sc, ec
		return None
	
	def inRange(self, x, y, select):
		if y < select["sy"] or y > select["ey"]:
			return False
		if y == select["sy"] and x < select["sx"]:
			return False
		if y == select["ey"] and x >= select["ex"]:
			return False
		return True
	
	@property
	def startX(self):
		return self.selections[-1][0] if self.selections else 0
	
	@property
	def startY(self):
		return self.selections[-1][1] if self.selections else 0