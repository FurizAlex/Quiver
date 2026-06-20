class CursorPoint:
	__slots__ = ("x", "y", "selectStartX", "selectStartY", "selectActive")

	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.selectStartX = x
		self.selectStartY = y
		self.selectActive = False

	def hasSelection(self):
		return self.selectActive and (self.selectStartX != self.x or self.selectStartY != self.y)
	
	def normalized(self):
		if (self.selectStartY, self.selectStartX) <= (self.y, self.x):
			return {"sx": self.selectStartX, "sy": self.selectStartY, "ex": self.x, "ey": self.y}
		else:
			return {"sx": self.x, "sy": self.y, "ex": self.selectStartX, "ey": self.selectStartY}
		
	def startSelection(self):
		self.selectStartX = self.x
		self.selectStartY = self.y
		self.selectActive = True

	def clearSelection(self):
		self.selectActive = False
		self.selectStartX = self.x
		self.selectStartY = self.y

class MultiCursor:
	def __init__(self, x=0, y=0):
		self.cursors = [CursorPoint(x, y)]

	@property
	def primary(self):
		return self.cursors[0]
	
	def reset(self, x, y):
		self.cursors = [CursorPoint(x, y)]

	def addCursor(self, x, y):
		for c in self.cursors:
			if c.x == x and c.y == y:
				return
		self.cursors.append(CursorPoint(x, y))
		self.sort()

	def removeDuplicates(self):
		primary = self.cursors[0]
		seen = set()
		unique = []
		for c in self.cursors:
			key = (c.x, c.y)
			if key not in seen:
				seen.add(key)
				unique.append(c)
		if not unique:
			unique = [CursorPoint(0, 0)]
		primaryKey = (primary.x, primary.y)
		for i, c in enumerate(unique):
			if (c.x, c.y) == primaryKey:
				unique[0], unique[i] = unique[i], unique[0]
				break
		self.cursors = unique

	def sort(self):
		self.cursors.sort(key=lambda c: (c.y, c.x))

	def isMulti(self):
		return len(self.cursors) > 1
	
	def collapseToPrimary(self):
		primary = self.cursors[0]
		self.cursors = [primary]

def forEachCursor(pane, fn, *args):
	cursors = pane.multiCursor.cursors
	if len(cursors) == 1:
		fn(pane.buffer, pane, *args)
		return
	for cursor in cursors:
		index = cursors.index(cursor)
		cursors[0], cursors[index] = cursors[index], cursors[0]
		fn(pane.buffer, pane, *args)
		cursors[0], cursors[index] = cursors[index], cursors[0]
	pane.multiCursor.sort()