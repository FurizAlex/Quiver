class History:
	def __init__(self):
		self.undo_stack = []
		self.redo_stack = []

	def push(self, bufferLines, x, y):
		state = (
			bufferLines.copy(),
			x,
			y
		)
		self.undo_stack.append(state)
		self.redo_stack.clear()

	def undo(self, currentState):
		if not self.undo_stack:
			return currentState

		self.redo_stack.append(currentState)
		return self.undo_stack.pop()

	def redo(self, currentState):
		if not self.redo_stack:
			return currentState

		self.undo_stack.append(currentState)
		return self.redo_stack.pop()