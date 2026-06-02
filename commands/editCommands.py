def undo(editor):
	buffer = editor.buffer
	pane = editor.pane

	currentState = (buffer.lines.copy(), pane.cursorX, pane.cursorY)

	state = editor.history.undo(currentState)

	buffer.lines = state[0].copy()
	
	pane.cursorX = state[1]
	pane.cursorY = state[2]

	buffer.ensureValid()

def redo(editor):
	buffer = editor.buffer
	pane = editor.pane

	currentState = (buffer.lines.copy(), pane.cursorX, pane.cursorY)

	state = editor.history.redo(currentState)

	buffer.lines = state[0].copy()
	
	pane.cursorX = state[1]
	pane.cursorY = state[2]

	buffer.ensureValid()