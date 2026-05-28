from util.fileio import saveFile

def handle(editor, key):
	if key == 27:
		editor.saving = False
		editor.status = ""
		return
	elif key == 10:
		filename = editor.saveInput.strip()

		if filename:
			editor.filename = filename
			
			editor.buffer.filename = filename

			editor.status = saveFile(filename, editor.buffer.lines)

			editor.buffer.modified = False
		editor.saving = False
	elif key in (8, 127):
		editor.saveInput = (editor.saveInput[:-1])
	elif 32 <= key <= 126:
		editor.saveInput += chr(key)
	editor.status = (
		"Save as: " + editor.saveInput
	)