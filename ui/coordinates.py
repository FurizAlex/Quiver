def screenToBuffer(editor, paneIndex, screenX, screenY):
	layout = editor.layout
	pane = editor.panes[paneIndex]

	startX = layout.textStartX(paneIndex)
	bufferY = pane.scrollY + screenY - 1

	line = editor.pane.buffer.lines[min(bufferY, len(editor.pane.buffer.lines) - 1)]
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

	lines = editor.pane.buffer.lines
	if not lines:
		return (0, 1)

	bufferY = max(0, min(bufferY, len(lines) - 1))
	line = lines[bufferY]
	visualX = 0

	for i, ch in enumerate(line[:bufferX]):
		if ch == "\t":
			tabSize = editor.settings.tabSize
			visualX += (tabSize - (visualX % tabSize))
		else:
			visualX += 1
	screenX = (layout.textStartX(paneIndex) + visualX - pane.scrollX)
	screenY = (bufferY - pane.scrollY + 1)

	return screenX, screenY