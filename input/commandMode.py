from util.fileio import openFile
from util.fileio import saveFile

from core.buffer import Buffer

def handle(editor, event):
	key = event.key

	if key == "ESC":
		editor.mode = "NORMAL"
		return
	elif key == "ENTER":
		command = editor.command.strip()
		if command == "q":
			editor.running = False
		elif command.startswith("o "):
			filename = command[2:].strip()
			newBuffer = Buffer(editor, filename)
			newBuffer.lines = openFile(filename)

			editor.buffers.append(newBuffer)
			editor.currentBuffer = len(editor.buffers) - 1

			editor.filename = filename
			editor.status = f"Opened {filename}"
		elif command == "w":
			if editor.filename:
				editor.status = saveFile(editor.filename, editor.pane.buffer.lines)
		editor.mode = "NORMAL"
	elif key == "BACKSPACE":
		editor.command = editor.command[:-1]
	elif len(key) == 1 and not event.ctrl:
		editor.command += key