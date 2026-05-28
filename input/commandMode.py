from util.fileio import openFile
from util.fileio import saveFile

from core.buffer import Buffer

def handle(editor, key):
	if key == 27:
		editor.mode = "NORMAL"
		return
	elif key == 10:
		command = editor.command.strip()

		if command == "q":
			editor.running = False

		elif command.startswith("o "):
			filename = command[2:].strip()

			newbuffer = Buffer(filename)
			newbuffer.lines = openFile(filename)

			editor.buffers.append(newbuffer)
			editor.currentBuffer = len(editor.buffers) - 1

			editor.filename = filename

			editor.status = f"Opened {filename}"
		elif command == "w":
			if editor.filename:
				editor.status = saveFile(
					editor.filename,
					editor.buffer.lines
				)
		editor.mode = "NORMAL"
	elif key == 127:
		editor.command = editor.command[:-1]
	elif 32 <= key <= 126:
		editor.command += chr(key)