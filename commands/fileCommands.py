from util.fileio import saveFile
from util.fileio import openFile

from core.buffer import Buffer

def save(editor):
	if editor.filename:
		result = saveFile(editor.filename, editor.buffers.lines)
		editor.buffer.modified = False
		editor.status = result
		editor.statusTimer = 120
	else:
		editor.saving = True
		editor.saveInput = ""
		editor.status = "Save as: "
	
def openFileBuffer(editor, filename):
	for i, buffer in enumerate(editor.buffers):
		if buffer.filename == filename:
			editor.currentBuffer = i
			editor.status = (f"Switched to {filename}")
			return
	newBuffer = Buffer()
	newBuffer.lines = openFile(filename)
	newBuffer.filename = filename
	
	newIndex = (len(editor.buffers) - 1)
	editor.buffers.append(newBuffer)
	editor.currentBuffer = newIndex
	editor.pane.bufferIndex = newIndex

	editor.status = f"Opened {filename}"