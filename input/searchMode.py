import curses

def findAllMatches(buffer, query):
	matches = []
	for lineIndex, line in enumerate(buffer.lines):
		start = 0
		while True:
			col = line.find(query, start)
			if col == -1:
				break
			matches.append((lineIndex, col, col + len(query)))
			start = col + 1
	return matches

def jumpToMatch(editor, matches, index):
	if not matches:
		return
	index = index % len(matches)
	lineIndex, sc, ec = matches[index]

	editor.selection.clear()
	editor.selection.begin(sc, lineIndex)
	editor.selection.update(ec, lineIndex)

	editor.pane.cursorY = lineIndex
	editor.pane.cursorX = ec

	centerToScreen(editor, lineIndex)

	editor.searchMatchIndex = index
	editor.status = f"SEARCH: {index + 1}/{len(matches)}"
	editor.statusTimer = 9999
	editor.notifyChanged()

def performSearch(editor):
	query = editor.searchInput
	buffer = editor.pane.buffer

	if not query:
		editor.searchMode = False
		editor.notifyChanged()
		return
	
	matches = findAllMatches(buffer, query)
	editor.searchMatches = matches
	editor.searchMatchIndex = 0

	if matches:
		jumpToMatch(editor, matches, 0)
	else:
		editor.selection.clear()
		editor.status = f"NOT FOUND: {query}"
		editor.statusTimer = 120
		editor.searchMatches = []
		editor.notifychanged()

def centerToScreen(editor, lineIndex):
	pane = editor.pane
	if hasattr(editor, "signals"):
		visibleLines = max(1, getattr(pane, "visibleLines", 30))
	else:
		visibleLines = editor.layout.paneVisibleHeight()
	half = visibleLines // 2
	target = max(0, lineIndex - half)
	maxScroll = max(0, len(pane.buffer.lines) - 1)
	pane.scrollY = min(target, maxScroll)

def selectAllMatches(editor):
	query = editor.searchInput
	buffer = editor.pane.buffer

	if not query:
		editor.searchMode = False
		editor.notifyChanged()
		return
	
	matches = findAllMatches(buffer, query)
	selection = editor.selection
	selection.clear()

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
		editor.status = f"SEARCH: {count} match{'es' if count != 1 else ''} selected"
		editor.statusTimer = 160
	else:
		editor.status = f"NOT FOUND: {query}"
		editor.statusTimer = 120
	editor.searchMode = False
	editor.searchInput = ""
	editor.searchMatches = []
	editor.notifyChanged()

def handle(editor, event):
	key = event.key

	if key == "ESC":
		editor.searchMode = False
		editor.searchInput = ""
		editor.searchMatches = []
		editor.selection.clear()
		editor.notifyChanged()
		return
	elif key == "ENTER":
		if event.ctrl:
			selectAllMatches(editor)
		elif not getattr(editor, "searchMatches", []):
			performSearch(editor)
		else:
			jumpToMatch(editor, editor.searchMatches, editor.searchMatchIndex + 1)
		return
	elif key == "LEFT":
		if getattr(editor, "searchMatches", []):
			jumpToMatch(editor, editor.searchMatches, editor.searchMatchIndex - 1)
		return
	elif key == "RIGHT":
		if getattr(editor, "searchMatches", []):
			jumpToMatch(editor, editor.searchMatches, editor.searchMatchIndex + 1)
		return
	elif key == "UP":
		if getattr(editor, "searchMatches", []):
			jumpToMatch(editor, editor.searchMatches, editor.searchMatchIndex - 1)
		return
	elif key == "DOWN":
		if getattr(editor, "searchMatches", []):
			jumpToMatch(editor, editor.searchMatches, editor.searchMatchIndex + 1)
		return
	elif key == "BACKSPACE":
		editor.searchInput = editor.searchInput[:-1]
		editor.searchMatches = []
		editor.notifyChanged()
	elif len(key) == 1 and not event.ctrl:
		editor.searchInput += key
		editor.searchMatches = []
		editor.notifyChanged()