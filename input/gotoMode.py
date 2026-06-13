import curses

def handle(editor, event):
	key = event.key

	if key == "ESC":
		editor.gotoMode = False
		editor.gotoInput = ""
		editor.status = ""
		return
	if key == "ENTER":
		try:
			line = int(editor.gotoInput.strip())
			index = max(0, min(line - 1, len(editor.pane.buffer.lines) - 1))
			editor.pane.cursorY = index
			editor.pane.cursorX = min(editor.pane.cursorX, len(editor.pane.buffer.lines[index]))
			editor.updateScroll()
			editor.status = f"Jumped to line {line}"
			editor.statusTimer = 60
		except ValueError:
			editor.status = "Invalid Line Number"
			editor.statusTimer = 60
		editor.gotoMode = False
		editor.gotoInput = ""
		editor.notifyChanged()
		return
	if key == "BACKSPACE":
		editor.gotoInput = editor.gotoInput[:-1]
	elif len(key) == 1 and key.isdigit():
		editor.gotoInput += key
	editor.status = f"Go to line! > {editor.gotoInput}_"
	editor.notifyChanged()