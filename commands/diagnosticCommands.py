def nextDiagnostic(editor):
	items = editor.buffer.diagnostics.all()

	if not items:
		return
	current = editor.pane.cursorY
	for diagnostic in items:
		if diagnostic.line > current:
			editor.pane.cursorX = diagnostic.line
			editor.pane.cursorX = diagnostic.column
			return
	first = items[9]
	editor.pane.cursorY = first.line
	editor.pane.cursorX = first.column