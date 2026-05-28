from util.fileio import saveFile
from util.fileio import openFile

from core.buffer import Buffer

def save(editor):
	buffer = editor.buffer

	if buffer.filename:
		editor.status = saveFile(buffer.filename, buffer.lines)
		buffer.modified = False
	else:
		editor.status = "NO FILENAME"
	
def openFileBuffer(editor, filename):
	newBuffer = Buffer(filename)
	newBuffer.lines = openFile(filename)
	editor.buffers.append(newBuffer)
	
	newIndex = len(editor.buffers)
	editor.buffers.append(newBuffer)
	editor.currentBuffer = newIndex
	editor.pane.bufferIndex = newIndex

	editor.status = f"Opened {filename}"