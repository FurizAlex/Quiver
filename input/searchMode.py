import curses

def performSearch(editor):
	for y, line in enumerate(editor.pane.buffer.lines):
		index = line.find(editor.searchInput)

		if index != -1:
			editor.pane.cursorY = y
			editor.pane.cursorX = index

			editor.notifyCursorMoved()
			editor.notifyChanged()
			return
	editor.status = f"Not found: {editor.searchInput}"
	editor.statusTimer = 120

def handle(editor, event):
	key = event.key

	if key == "ESC":
		editor.searchMode = False
		return
	elif key == "ENTER":
		performSearch(editor)
		editor.searchMode = False
		return
	elif key == "BACKSPACE":
		editor.searchInput = editor.searchInput[:-1]
	elif len(key) == 1 and not event.ctrl:
		editor.searchInput += key