import curses

def handle(editor, event):
	key = event.key

	if key == "ESC":
		editor.gotoMode = False
		return
	elif key == "ENTER":
		try:
			line = int(editor.gotoInput) - 1
			line = max(0, min(line, len(editor.pane.buffer.lines) - 1))
		except ValueError:
			pass
		editor.gotoMode = False
		return
	elif key == "BACKSPACE":
		editor.gotoInput = editor.gotoInput[:-1]
	elif len(key) == 1 and key.isdigit():
		editor.gotoInput += key