import curses

def handle(editor):
	try:
		_, mx, my, _, state = (curses.getmouse())
	except:
		return
	
	lineNumberWidth = 6
	editorOffsetX = 1

	if editor.showExplorer:
		if mx < editor.explorerWidth:
			editor.focus = "explorer"
			index = my - 3

			if (0 <= index < len(editor.explorerFiles)):
				editor.selectedFileIndex = index
			return
	editor.focus = "editor"

	cursorX = (mx - lineNumberWidth - editorOffsetX)
	cursorY = (my - 1 + editor.pane.scrollY)

	cursorX = max(0, cursorX)
	cursorY = max(0, cursorY)

	cursorY = min(cursorY, len(editor.buffer.lines) - 1)

	lineLength = len(editor.buffer.lines[cursorY])

	cursorX = min(cursorX, lineLength)

	editor.pane.cursorX = cursorX
	editor.pane.cursorY = cursorY

	if state & curses.BUTTON1_PRESSED:
		editor.selection.begin(cursorX, cursorY)
	elif state & curses.BUTTON1_RELEASED:
		editor.selection.update(cursorX, cursorY)
	elif state & curses.BUTTON1_CLICKED:
		editor.selection.clear()
	elif hasattr(curses, "BUTTON1_MOVED"):
		if state & curses.BUTTON1_MOVED:
			editor.selection.update(cursorX, cursorY)
