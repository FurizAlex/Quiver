def saveUndo(editor):
	buffer = editor.buffer
	pane = editor.pane

	editor.history.push(buffer.lines.copy(), pane.cursorX, pane.cursorY)