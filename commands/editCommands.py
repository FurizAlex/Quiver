def undo(editor):
	buffer = editor.pane.buffer
	pane = editor.pane

	currentState = (buffer.lines.copy(), pane.cursorX, pane.cursorY)

	state = editor.history.undo(currentState)

	buffer.lines = state[0].copy()
	
	pane.cursorX = state[1]
	pane.cursorY = state[2]

	buffer.ensureValid()

	editor.status = "UNDO"
	editor.statusTimer = 60
	editor.notifyChanged()

def redo(editor):
	buffer = editor.pane.buffer
	pane = editor.pane

	currentState = (buffer.lines.copy(), pane.cursorX, pane.cursorY)

	state = editor.history.redo(currentState)

	buffer.lines = state[0].copy()
	
	pane.cursorX = state[1]
	pane.cursorY = state[2]

	buffer.ensureValid()

	editor.status = "REDO"
	editor.statusTimer = 60
	editor.notifyChanged()