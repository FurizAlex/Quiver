import curses
from util.fileio import saveFile

def handle(editor, key):
	if key == 27:
		editor.saving = False
		editor.status = ""
		return
	elif key in (10, 13, curses.KEY_ENTER):
		filename = editor.saveInput.strip()

		if filename:
			editor.filename = filename
			
			editor.pane.buffer.filename = filename

			from syntax.filetypes import detect

			editor.pane.buffer.language = detect(filename)

			editor.pane.buffer.modified = False
			editor.status = saveFile(filename, editor.pane.buffer.lines)
			editor.statusTimer = 120
		editor.saving = False
		return
	elif key in (8, 127, curses.KEY_BACKSPACE):
		editor.saveInput = (editor.saveInput[:-1])
	elif 32 <= key <= 126:
		editor.saveInput += chr(key)
	editor.status = (
		"Save as: " + editor.saveInput
	)