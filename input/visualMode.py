import curses

def handle(editor, key):
	cursor = editor.pane.cursor
	selection = editor.selection
	buffer = editor.pane.buffer

	match key:
		case 27:
			editor.mode = "NORMAL"
			selection.clear()
		case curses.KEY_LEFT:
			cursor.moveLeft()
		case curses.KEY_RIGHT:
			line = buffer.currentLine(cursor.y)
			cursor.moveRight(len(line))
		case curses.KEY_UP:
			cursor.moveUp()
		case curses.KEY_DOWN:
			cursor.moveDown(len(buffer.lines))
	selection.update(cursor.x, cursor.y)