from core.cursor import Cursor
from core.viewport import Viewport

class Pane:
	def __init__(self, bufferIndex=0):
		self.bufferIndex = bufferIndex
		
		self.cursor = Cursor()
		self.viewport = Viewport()

	def moveLeft(self):
		self.cursorX = max(0, self.cursorX - 1)

	def moveRight(self, lineLength):
		self.cursorX = min(
			lineLength,
			self.cursorX + 1
		)

	def moveUp(self):
		self.cursorY = max(0, self.cursorY - 1)

	def moveDown(self, maxLines):
		self.cursorY = min(
			maxLines - 1,
			self.cursorY + 1
		)

	@property
	def x(self):
		return self.cursorX
	
	@x.setter
	def x(self, value):
		self.cursorX = value
	
	@property
	def y(self):
		return self.cursorY
	
	@y.setter
	def y(self, value):
		self.cursorY = value

	@property
	def scrollX(self):
		return self.viewport.scrollX

	@scrollX.setter
	def scrollX(self, value):
		self.viewport.scrollX = value

	@property
	def scrollY(self):
		return self.viewport.scrollY
	
	@scrollY.setter
	def scrollY(self, value):
		self.viewport.scrollY = value

	@property
	def cursorX(self):
		return self.cursor.x
	
	@cursorX.setter
	def cursorX(self, value):
		self.cursor.x = value
	
	@property
	def cursorY(self):
		return self.cursor.y
	
	@cursorY.setter
	def cursorY(self, value):
		self.cursor.y = value