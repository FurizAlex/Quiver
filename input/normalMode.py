import curses

from util.helpers import nextWordStart
from util.helpers import nextWordEnd
from util.helpers import prevWordStart

def handle(editor, key):
	cursor = editor.cursor
	buffer = editor.buffer

	if key == ord('q'):
		editor.running = False

	elif key == ord('i'):
		editor.mode = "EDIT"
		editor.status = "EDIT MODE"

	elif key == ord('v'):
		editor.mode = "VISUAL"
		editor.selection.begin(cursor.x, cursor.y)
	
	elif key == ord('w'):
		line = buffer.currentLine(cursor.y)
		cursor.x = nextWordStart(line, cursor.x)

	elif key == ord('e'):
		line = buffer.currentLine(cursor.y)
		cursor.x = nextWordEnd(line, cursor.x)

	elif key == ord('b'):
		line = buffer.currentLine(cursor.y)
		cursor.x = prevWordStart(line, cursor.x)

	elif key == ord(':'):
		editor.mode = "COMMAND"
		editor.command = ""

	elif key == curses.KEY_LEFT:
		cursor.moveLeft()

	elif key == curses.KEY_RIGHT:
		line = buffer.currentLine(cursor.y)
		cursor.moveRight(len(line))

	elif key == curses.KEY_UP:
		cursor.moveUp()

		line = buffer.currentLine(cursor.y)
		cursor.x = min(cursor.x, len(line))

	elif key == curses.KEY_DOWN:
		cursor.moveDown(len(buffer.lines))

		line = buffer.currentLine(cursor.y)
		cursor.x = min(cursor.x, len(line))