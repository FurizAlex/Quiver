def saveUndo(editor):
	buffer = editor.pane.buffer
	pane = editor.pane

	editor.history.push(buffer.lines.copy(), pane.cursorX, pane.cursorY)