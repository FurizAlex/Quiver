import os
from util.fileio import saveFile

def handle(editor, event):
	key = event.key

	if key == "ESC":
		editor.saving = False
		editor.status = ""
		return
	elif key == "ENTER":
		filename = editor.saveInput.strip()
		if filename:
			if not os.path.dirname(filename):
				filename = os.path.join(os.path.abspath(editor.explorerPath), filename)
			filename = os.path.abspath(filename)
			editor.pane.buffer.filename = filename
			editor.pane.buffer.language = editor.languageRegistry.detect(filename)
			editor.pane.buffer.modified = False
			editor.status = saveFile(filename, editor.pane.buffer.lines)
			editor.statusTimer = 120
			editor.refreshExplorer()
		editor.saving = False
		return
	elif key == "BACKSPACE":
		editor.saveInput = editor.saveInput[:-1]
	elif len(key) == 1 and not event.ctrl:
		editor.saveInput += key
	editor.status = "Save as: " + editor.saveInput