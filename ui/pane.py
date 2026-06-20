from core.cursor import Cursor
from core.viewport import Viewport
from core.multiCursor import MultiCursor

class Pane:
	def __init__(self, buffer=None):
		self.buffer = buffer
		self.viewport = Viewport()
		self.multiCursor = MultiCursor()

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
		return self.multiCursor.primary.x
	
	@cursorX.setter
	def cursorX(self, value):
		self.multiCursor.primary.x = value
	
	@property
	def cursorY(self):
		return self.multiCursor.primary.y
	
	@cursorY.setter
	def cursorY(self, value):
		self.multiCursor.primary.y = value