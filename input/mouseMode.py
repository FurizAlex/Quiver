import curses
from ui.coordinates import screenToBuffer

def handleMouse(editor):
	try:
		_, mx, my, _, state = curses.getmouse()
	except:
		return

	if editor.showExplorer:
		if mx < editor.explorerWidth:
			editor.focus = "explorer"

			index = my - 3
			if 0 <= index < len(editor.explorerFiles):
				editor.selectedFileIndex = index
			return
	editor.focus = "editor"

	bufferX, bufferY = screenToBuffer(editor, editor.activePane, mx, my)
	bufferY = max(0, bufferY)
	bufferY = min(bufferY, len(editor.buffer.lines) - 1)

	lineLength = len(editor.buffer.lines[bufferY])
	bufferX = max(0, min(bufferX, lineLength))

	editor.pane.cursorX = bufferX
	editor.pane.cursorY = bufferY

	if state & curses.BUTTON1_PRESSED:
		editor.selection.begin(bufferX, bufferY)
	elif state & curses.BUTTON1_RELEASED or state & curses.BUTTON1_PRESSED or state & curses.BUTTON1_CLICKED:
		if editor.selection.active:
			editor.selection.update(bufferX, bufferY)
	elif state & curses.BUTTON1_CLICKED:
		editor.selection.clear()