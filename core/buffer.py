class Buffer:
	def __init__(self):
		self.lines = [""]

	def currentLine(self, y):
		return self.lines[y]

	def insertChar(self, x, y, char):
		line = self.lines[y]

		self.lines[y] = (
			line[:x] +
			char +
			line[x:]
		)

	def deleteChar(self, x, y):
		line = self.lines[y]
	
		if x > 0:
			self.lines[y] = (
				line[:x - 1] +
				line[x:]
			)

	def splitLine(self, x, y):
		line = self.lines[y]

		left = line[:x]
		right = line[x:]

		self.lines[y] = left
		self.lines.insert(y + 1, right)

	def mergeLine(self, y):
		if y <= 0:
			return

		prev = self.lines[y - 1]
		current = self.lines[y]

		self.lines[y - 1] = prev + current
		self.lines.pop(y)