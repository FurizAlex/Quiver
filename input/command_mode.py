from util.fileio import open_file
from util.fileio import save_file

def handle(editor, key):
	if key == 27:
		editor.mode = "NORMAL"
		return
	elif key == 10:
		command = editor.command.strip()

		if command == "q":
			editor.running = false

		elif command.startswith("o "):
			filename = command[2:].strip()

			editor.buffer.lines = open_file(filename)

			editor.filename = filename

			editor.status = f"Opened {filename}"
		elif command == "w":
			if editor.filename:
				editor.status = save_file(
					editor.filename,
					editor.buffer.lines
				)
		editor.mode = "NORMAL"
	elif key == 127:
		editor.command = editor.command[:-1]
	elif 32 <= key <= 126:
		editor.command += chr(key)