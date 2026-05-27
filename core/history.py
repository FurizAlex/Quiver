class History:
	def __init__(self):
		self.undoStack = []
		self.redoStack = []

	def push(self, lines, x, y):
		state = (
			lines.copy(),
			x,
			y
		)
		self.undoStack.append(state)
		self.redoStack.clear()

	def undo(self, currentState):
		if not self.undoStack:
			return currentState

		self.redoStack.append(currentState)
		return self.undoStack.pop()

	def redo(self, currentState):
		if not self.redoStack:
			return currentState

		self.undoStack.append(currentState)
		return self.redoStack.pop()