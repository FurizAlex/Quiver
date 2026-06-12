import os
from ui.coordinates import screenToBuffer
from commands.fileCommands import openFileBuffer

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
				editor.notifyChanged()
				return
			x += len(title) + 1
		return
	if state == "WHEEL_UP":
		editor.pane.scrollY = max(0, editor.pane.scrollY - 3)
		return
	if state == "WHEEL_DOWN":
		maxScroll = max(0, len(editor.pane.buffer.lines) - 1)
		editor.pane.scrollY = min(maxScroll, editor.pane.scrollY + 3)
		return
	if editor.showExplorer and mx < editor.explorerWidth:
		editor.focus = "explorer"
		index = my - 3
		if 0 <= index < len(editor.explorerFiles):
			editor.selecteddFileIndex = index
			selected = editor.explorerFiles[index]
			path = os.path.join(editor.explorerPath, selected)
			if os.path.isdir(path):
				editor.explorerPath = path
				editor.refreshExplorer()
				editor.selectedFileIndex = 0
			else:
				openFileBuffer(editor, path)
				editor.focus = "editor"
		return
	editor.focus = "editor"
	bufferX, bufferY = screenToBuffer(editor, editor.activePane, mx, my)
	bufferY = max(0, min(bufferY, len(editor.pane.buffer.lines) - 1))
	lineLength = len(editor.pane.buffer.lines[bufferY])
	bufferX = max(0, min(bufferX, lineLength))
	editor.pane.cursorX = bufferX
	editor.pane.cursorY = bufferY

	if state == "LEFT_PRESS":
		editor.selection.begin(bufferX, bufferY)
	elif state == "LEFT_RELEASE":
		if editor.selection.active:
			editor.selection.update(bufferX, bufferY)
	elif state == "LEFT_CLICK":
		editor.selection.clear()
