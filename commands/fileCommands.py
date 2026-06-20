import os

from util.fileio import saveFile
from util.fileio import openFile

from core.buffer import Buffer

def save(editor):
	if editor.pane.buffer.filename:
		result = saveFile(editor.pane.buffer.filename, editor.pane.buffer.lines)
		editor.pane.buffer.modified = False
		editor.status = result
		editor.statusTimer = 120
		invalidateDiffCache(editor, editor.pane.buffer)
	else:
		editor.saving = True
		editor.saveInput = ""
		editor.status = "Save as: "
	editor.plugins.dispatchSave(editor)

def invalidateDiffCache(editor, buffer):
	if not editor.settings.gitDiffEnabled:
		return
	if hasattr(editor, "qtWindow"):
		for view in editor.qtWindow.views.paneContainer.paneViews:
			if view.pane.buffer is buffer:
				view.diffCacheFile = None
	
def openFileBuffer(editor, filename):
	absFilename = os.path.abspath(filename)
	for i, buffer in enumerate(editor.buffers):
		if buffer.filename and os.path.abspath(buffer.filename) == absFilename:
			editor.currentBuffer = i
			editor.pane.buffer = editor.buffers[i]
			editor.pane.cursorY = min(editor.pane.cursorY, len(editor.buffers[i].lines) - 1)
			editor.pane.cursorX = min(editor.pane.cursorX, len(editor.buffers[i].lines[editor.pane.cursorY]))
			editor.status = (f"Switched to {filename}")
			trackRecent(editor, filename)
			return
	newBuffer = Buffer(editor, filename)
	newBuffer.language = editor.languageRegistry.detect(filename)
	newBuffer.lines = openFile(filename)
	newBuffer.filename = filename
	
	if not newBuffer.lines:
		newBuffer.lines = [""]
	editor.buffers.append(newBuffer)
	
	newIndex = len(editor.buffers) - 1
	editor.currentBuffer = newIndex
	editor.pane.buffer = newBuffer

	editor.plugins.dispatchOpen(editor, filename)
	editor.plugins.dispatchBufferCreated(editor, newBuffer)

	editor.pane.cursorX = 0
	editor.pane.cursorY = 0

	editor.status = f"Opened {filename}"
	trackRecent(editor, filename)
	editor.notifyChanged()

def trackRecent(editor, filename):
	absPath = os.path.abspath(filename)
	recents = getattr(editor, "recentFiles", [])
	if absPath in recents:
		recents.remove(absPath)
	recents.insert(0, absPath)
	editor.recentFiles = recents[:10]
	editor.settings.set("recentFiles", editor.recentFiles)