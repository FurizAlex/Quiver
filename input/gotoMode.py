import curses

def handle(editor, key):
	if key == 27:
		editor.gotoMode = False
		return
	elif key in (10, 13):
		try:
			line = int(editor.gotoInput)
			line -= 1
			line = max(0, min(line, len(editor.buffers.lines) - 1))
			editor.pane.cursor.cursorY = line
			editor.pane.cursor.cursorX = 0
		except:
			pass
		editor.gotoMode = False
		return
	elif key in (8, 127, curses.KEY_BACKSPACE):
		editor.gotoInput = editor.gotoInput[:-1]
	elif chr(key).isdigit():
		editor.gotoInput += chr(key)