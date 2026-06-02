from util.fileio import saveFile
from util.fileio import openFile

from core.buffer import Buffer

def save(editor):
	if editor.buffer.filename:
		result = saveFile(editor.buffer.filename, editor.buffer.lines)
		editor.buffer.modified = False
		editor.status = result
		editor.statusTimer = 120
	else:
		editor.saving = True
		editor.saveInput = ""
		editor.status = "Save as: "
	editor.plugins.dispatchSave(editor)
	
def openFileBuffer(editor, filename):
	for i, buffer in enumerate(editor.buffers):
		if buffer.filename == filename:
			editor.currentBuffer = i
			editor.pane.bufferIndex = i
			editor.status = (f"Switched to {filename}")
			return
	newBuffer = Buffer()
	newBuffer.language = editor.languageRegistry.detect(filename)
	newBuffer.lines = openFile(filename)
	newBuffer.filename = filename
	
	if not newBuffer.lines:
		newBuffer.lines = [""]
	editor.buffers.append(newBuffer)
	
	newIndex = len(editor.buffers) - 1
	editor.currentBuffer = newIndex
	editor.pane.bufferIndex = newIndex

	editor.plugins.dispatchOpen(editor, filename)
	editor.plugins.dispatchBufferCreated(editor, newBuffer)

	editor.pane.cursorX = 0
	editor.pane.cursorY = 0

	editor.status = f"Opened {filename}"