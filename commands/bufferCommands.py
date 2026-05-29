def nextBuffer(editor):
	if not editor.buffers:
		return
	editor.currentBuffer = ((editor.currentBuffer + 1) % len(editor.buffers))
	editor.pane.bufferIndex = editor.currentBuffer
	clampCursors(editor)

def previousBuffer(editor):
	if not editor.buffers:
		return
	editor.currentBuffer = ((editor.currentBuffer - 1) % len(editor.buffers))
	editor.pane.bufferIndex = editor.currentBuffer
	clampCursors(editor)

def clampCursors(editor):
	buffer = editor.buffer
	pane = editor.pane

	pane.cursorY = min(pane.cursorY, len(buffer.lines) - 1)
	pane.cursorY = max(0, pane.cursorY)

	line = buffer.lines[pane.cursorY]

	pane.cursorX = min(pane.cursorX, len(line))
	pane.cursorX = max(0, pane.cursorX)