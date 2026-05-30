class Buffer:
	def __init__(self, filename=None):
		self.filename = filename

		self.lines = [""]
		self.modified = False

	@property
	def name(self):
		if self.filename:
			import os
			return os.path.basename(self.filename)

		return "UNTITLED"

	def currentLine(self, y):
		return self.lines[y]

	def insertChar(self, x, y, char):
		if not self.lines:
			self.lines = [""]
		line = self.lines[y]

		self.lines[y] = (
			line[:x] +
			char +
			line[x:]
		)
		self.modified = True

	def deleteChar(self, x, y):
		line = self.lines[y]
	
		self.lines[y] = (
			line[:x - 1] + line[x:]
		)
		self.modified = True

	def splitLine(self, x, y):
		line = self.lines[y]

		self.lines[y] = line[:x]
		self.lines.insert(y + 1, line[x:])
		self.modified = True

	def mergeLine(self, y):
		self.lines[y - 1] += self.lines[y]
		self.lines.pop(y)
		self.modified = True

	def getSelection(self, sx, sy, ex, ey):
		lines = []

		for y in range(sy, ey + 1):
			line = self.lines[y]

			if y == sy and y == ey:
				lines.append(line[sx:ex])
			elif y == sy:
				lines.append(line[sx:])
			elif y == ey:
				lines.append(line[:ex])
			else:
				lines.append(line)
		return "\n".join(lines)

	def ensureValid(self):
		if not self.lines:
			self.lines = [""]