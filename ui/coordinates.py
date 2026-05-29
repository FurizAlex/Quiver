def screenToBuffer(editor, paneIndex, screenX, screenY):
	layout = editor.layout
	pane = editor.panes[paneIndex]

	startX = layout.textStartX(paneIndex)
	bufferY = pane.scrollY + screenY - 1

	line = editor.buffer.lines[min(bufferY, len(editor.buffer.lines) - 1)]
	relativeX = screenX - startX
	bufferX = 0
	visualX = 0

	for ch in line:
		width = (
			editor.settings.tabSize
			if ch == "\t"
			else 1
		)
		if visualX + width > relativeX:
			break
		visualX += width
		bufferX += 1
	return (bufferX, bufferY)

def bufferToScreen(editor, paneIndex, bufferX, bufferY):
	layout = editor.layout
	pane = editor.panes[paneIndex]

	screenX = (layout.textStartX(paneIndex) + bufferX)
	screenY = (bufferY - pane.scrollY + 1)

	return screenX, screenY