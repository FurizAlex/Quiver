def nextBuffer(editor):
	pane = editor.pane

	pane.bufferIndex = (pane.bufferIndex + 1) % len(editor.buffers)
	editor.currentBuffer = pane.bufferIndex
	clampCursors(editor)

def previousBuffer(editor):
	pane = editor.pane

	pane.bufferIndex = (pane.bufferIndex - 1) % len(editor.buffers)
	editor.currentBuffer = pane.bufferIndex
	clampCursors(editor)

def closeBuffer(editor):
	if len(editor.buffers) == 1:
		editor.status = "Cannot close last buffer"
		return
	closing = editor.currentBuffer
	editor.buffers.pop(closing)

	for pane in editor.panes:
		if pane.bufferIndex > closing:
			pane.bufferIndex -= 1
		elif pane.bufferIndex == closing:
			pane.bufferIndex = max(0, min(pane.bufferIndex, len(editor.buffers) - 1))
	editor.currentBuffer = min(editor.currentBuffer, len(editor.buffers) - 1)
	editor.status = "Tab Closed"

def clampCursors(editor):
	if editor.pane.bufferIndex >= len(editor.buffers):
		editor.pane.bufferIndex = len(editor.buffers) - 1
	if editor.pane.bufferIndex < 0:
		editor.pane.bufferIndex = 0

	buffer = editor.buffer
	pane = editor.pane

	pane.cursorY = min(pane.cursorY, len(buffer.lines) - 1)
	pane.cursorY = max(0, pane.cursorY)

	line = buffer.lines[pane.cursorY]

	pane.cursorX = min(pane.cursorX, len(line))
	pane.cursorX = max(0, pane.cursorX)