import os

MAX_CLOSED = 20


def flash(editor, message, ticks=120):
	editor.status = message
	editor.statusTimer = ticks
	editor.notifyChanged()


def _viewStates(editor):
	return editor.__dict__.setdefault("_viewStates", {})


def rememberView(editor, pane, buffer):
	"""Remember where the cursor/scroll was in a buffer so switching back restores it."""
	_viewStates(editor)[id(buffer)] = (
		pane.cursorX,
		pane.cursorY,
		getattr(pane, "scrollX", 0),
		getattr(pane, "scrollY", 0),
	)


def restoreView(editor, pane, buffer):
	cx, cy, sx, sy = _viewStates(editor).get(id(buffer), (0, 0, 0, 0))
	lastLine = max(0, len(buffer.lines) - 1)
	cy = max(0, min(cy, lastLine))
	cx = max(0, min(cx, len(buffer.lines[cy])))
	pane.cursorX = cx
	pane.cursorY = cy
	pane.scrollX = max(0, sx)
	pane.scrollY = max(0, min(sy, lastLine))
	pane.multiCursor.reset(cx, cy)


def activeIndex(editor):
	"""Index of the buffer shown in the active pane (the truth for 'which tab is active')."""
	try:
		return editor.buffers.index(editor.pane.buffer)
	except ValueError:
		return max(0, min(editor.currentBuffer, len(editor.buffers) - 1))


def syncCurrent(editor):
	editor.currentBuffer = activeIndex(editor)


def switchToBuffer(editor, index):
	buffers = editor.buffers
	if not (0 <= index < len(buffers)):
		return False
	pane = editor.pane
	old = pane.buffer
	new = buffers[index]
	if old is not new:
		rememberView(editor, pane, old)
		pane.buffer = new
		restoreView(editor, pane, new)
		editor.selection.clear()
	editor.currentBuffer = index
	editor.completionActive = False
	editor.completions = []
	editor._undoGroup = None
	scrollX = pane.scrollX
	editor.updateScroll()
	pane.scrollX = scrollX      # horizontal scroll is owned by the view (visual columns)
	editor.notifyChanged()
	return True


def nextBuffer(editor):
	count = len(editor.buffers)
	if count > 1:
		switchToBuffer(editor, (activeIndex(editor) + 1) % count)


def previousBuffer(editor):
	count = len(editor.buffers)
	if count > 1:
		switchToBuffer(editor, (activeIndex(editor) - 1) % count)


def moveBuffer(editor, src, dst):
	"""Reorder tabs (insert, not swap) while keeping the active tab active."""
	buffers = editor.buffers
	if src == dst or not (0 <= src < len(buffers)) or not (0 <= dst < len(buffers)):
		return False
	buffers.insert(dst, buffers.pop(src))
	syncCurrent(editor)
	editor.notifyChanged()
	return True


def _makeBlankBuffer(editor):
	from core.buffer import Buffer
	return Buffer(editor=editor, language=editor.languageRegistry.get("text"))


def _rememberClosed(editor, buffer):
	if not buffer.filename:
		return
	stack = editor.__dict__.setdefault("_closedBuffers", [])
	path = os.path.abspath(buffer.filename)
	if path in stack:
		stack.remove(path)
	stack.append(path)
	del stack[:-MAX_CLOSED]


def removeBuffer(editor, index, remember=True):
	"""Remove a buffer without any prompting. Every pane showing it is moved to a neighbour.
	Closing the only buffer leaves a fresh blank one."""
	buffers = editor.buffers
	if not (0 <= index < len(buffers)):
		return
	removed = buffers[index]
	if len(buffers) == 1 and not removed.filename and removed.lines == [""]:
		removed.modified = False
		return
	if remember:
		_rememberClosed(editor, removed)
	if len(buffers) == 1:
		replacement = _makeBlankBuffer(editor)
		buffers[0] = replacement
	else:
		buffers.pop(index)
		replacement = buffers[min(index, len(buffers) - 1)]
	_viewStates(editor).pop(id(removed), None)
	for pane in editor.panes:
		if pane.buffer is removed:
			pane.buffer = replacement
			restoreView(editor, pane, replacement)
	editor.selection.clear()
	editor.completionActive = False
	editor.completions = []
	editor._undoGroup = None
	syncCurrent(editor)
	editor.updateScroll()
	editor.notifyChanged()


def reopenClosedBuffer(editor):
	stack = editor.__dict__.setdefault("_closedBuffers", [])
	while stack:
		path = stack.pop()
		if os.path.exists(path):
			from commands.fileCommands import openFileBuffer
			openFileBuffer(editor, path)
			if not editor.pane.buffer.lines:
				editor.pane.buffer.lines.append("")
			syncCurrent(editor)
			flash(editor, f"Reopened {os.path.basename(path)}")
			return True
	flash(editor, "No closed tabs to reopen")
	return False


def buffersUnder(editor, path):
	"""Buffers whose file is `path` or lives inside the folder `path`."""
	base = os.path.normcase(os.path.abspath(path))
	found = []
	for buffer in editor.buffers:
		if not buffer.filename:
			continue
		full = os.path.normcase(os.path.abspath(buffer.filename))
		if full == base or full.startswith(base + os.sep):
			found.append(buffer)
	return found


def saveBufferToDisk(editor, buffer, parent=None):
	"""Save without going through the in-editor Save-As prompt.
	Unnamed buffers get a native Save dialog. Returns False if the user cancelled / it failed."""
	from util.fileio import saveFile
	if not buffer.filename:
		from PyQt6.QtWidgets import QFileDialog
		folder = getattr(editor, "explorerPath", None) or os.path.expanduser("~")
		path, _ = QFileDialog.getSaveFileName(parent, "Save As", os.path.join(folder, "untitled.txt"))
		if not path:
			return False
		buffer.filename = path
	try:
		saveFile(buffer.filename, buffer.lines)
	except Exception as e:
		flash(editor, f"Save failed: {e}")
		return False
	buffer.modified = False
	editor.notifyChanged()
	return True