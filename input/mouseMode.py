import curses
from ui.coordinates import screenToBuffer

def handleMouse(editor, event):
	mx = event.mouseX
	my = event.mouseY
	state = event.button

	if my == 0:
		x = 2
		for i, buffer in enumerate(editor.buffers):
			title = f" {buffer.name} "

			if buffer.modified:
				title += "* "
			if x <= mx < x + len(title):
				editor.currentBuffer = i
				editor.pane.buffer = editor.buffers[i]
			x += len(title) + 1
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
	bufferY = min(bufferY, len(editor.pane.buffer.lines) - 1)

	lineLength = len(editor.pane.buffer.lines[bufferY])
	bufferX = max(0, min(bufferX, lineLength))

	editor.pane.cursorX = bufferX
	editor.pane.cursorY = bufferY

	if state == "LEFT_PRESS":
		editor.selection.begin(bufferX, bufferY)
	elif state == "LEFT_RELEASE":
		if editor.selection.active:
			editor.selection.update(bufferX, bufferY)
	#elif state & curses.BUTTON1_MOVED:
	#	if editor.selection.active:
	#		editor.selection.update(bufferX, bufferY)
	elif state == "LEFT_CLICK":
		editor.selection.clear()

	if state == "WHEEL_UP":
		editor.scrollY = max(0, editor.scrollY - 3)
		return
	if state == "WHEEL_DOWN":
		editor.scrollY += 3
		return