def nextBuffer(editor):
	pane = editor.pane

	editor.currentBuffer = (editor.currentBuffer + 1) % len(editor.buffers)
	pane.buffer = editor.buffers[editor.currentBuffer]

def previousBuffer(editor):
	pane = editor.pane

	editor.currentBuffer = (editor.currentBuffer - 1) % len(editor.buffers)
	pane.buffer = editor.buffers[editor.currentBuffer]

def closeBuffer(editor):
	if len(editor.buffers) == 1:
		editor.status = "Cannot close last buffer"
		return
	closing = editor.currentBuffer
	editor.buffers.pop(closing)

	closingBuffer = editor.buffers[closing]
	editor.buffers.pop(closing)
	replacement = editor.buffers[min(closing, len(editor.buffers) - 1)]
	for pane in editor.panes:
		if pane.buffer is closingBuffer:
			pane.buffer = replacement
	editor.currentBuffer = min(editor.currentBuffer, len(editor.buffers) - 1)
	editor.status = "Tab Closed"