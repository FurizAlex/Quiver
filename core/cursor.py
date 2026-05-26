class Cursor:
	def __init__(self):
		self.x = 0
		self.y = 0

	def moveLeft(self):
		self.x = max(0, self.x - 1)

	def moveRight(self, lineLength):
		self.x = min(lineLength, self.x + 1)

	def moveUp(self):
		self.y = max(0, self.y - 1)
	
	def moveDown(self, bufferLength):
		self.y = min(bufferLength - 1, self.y + 1)