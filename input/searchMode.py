import curses

def performSearch(editor):
	query = editor.searchInput
	buffer = editor.pane.buffer

	if not query:
		editor.searchMode = False
		editor.notifyChanged()
		return
	
	selection = editor.selection
	selection.clear()
	matches = []

	for lineIndex, line in enumerate(buffer.lines):
		start = 0
		while True:
			col = line.find(query, start)
			if col == -1:
				break
			matches.append((lineIndex, col, col + len(query)))
			start = col + 1
	if matches:
		for i, (lineIndex, sc, ec) in enumerate(matches):
			if i == 0:
				selection.begin(sc, lineIndex)
				selection.update(ec, lineIndex)
			else:
				selection.addSelection(sc, lineIndex, ec, lineIndex)
		editor.pane.cursorY = matches[0][0]
		editor.pane.cursorX = matches[0][2]
		editor.updateScroll()
		count = len(matches)
		editor.status = f"SEARCH: {count} match{'es' if count != 1 else ''}"
		editor.statusTimer = 180
	else:
		editor.status = f"NOT FOUND: {query}"
		editor.statusTimer = 120
	editor.searchMode = False
	editor.searchInput = ""
	editor.notifyChanged()

def handle(editor, event):
	key = event.key

	if key == "ESC":
		editor.searchMode = False
		editor.searchInput = ""
		editor.notifyChanged()
		return
	elif key == "ENTER":
		performSearch(editor)
		return
	elif key == "BACKSPACE":
		editor.searchInput = editor.searchInput[:-1]
		editor.notifyChanged()
	elif len(key) == 1 and not event.ctrl:
		editor.searchInput += key
		editor.notifyChanged()