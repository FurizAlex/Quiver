import curses

def performSearch(editor):
	for y, line in enumerate(editor.buffer.lines):
		index = line.find(editor.searchInput)

		if index != -1:
			editor.cursor.cursorY = y
			editor.cursor.cursorX = index
			return
	editor.status = f"Not found: {editor.searchInput}"
	editor.statusTimer = 120

def handle(editor, key):
	if key == 27:
		editor.searchMode = False
		return
	elif key in (10, 13):
		performSearch(editor)
		editor.searchMode = False
		return
	elif key in (8, 127, curses.KEY_BACKSPACE):
		editor.searchInput = editor.searchInput[:-1]
	elif 32 <= key <= 126:
		editor.searchInput += chr(key)