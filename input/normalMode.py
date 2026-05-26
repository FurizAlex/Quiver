import curses

def handle(editor, key):
	cursor = editor.cursor
	buffer = editor.buffer

	match key:
		case ord('q'):
			editor.running = False

		case ord('i'):
			editor.mode = "EDIT"
			editor.status = "EDIT MODE"

		case ord(':'):
			editor.mode = "COMMAND"
			editor.command = ""

		case curses.KEY_LEFT:
			cursor.move_left()

		case curses.KEY_RIGHT:
			line = buffer.current_line(cursor.y)
			cursor.move_right(len(line))

		case curses.KEY_UP:
			cursor.move_up()

			line = buffer.current_line(cursor.y)
			cursor.x = min(cursor.x, len(line))

		case curses.KEY_DOWN:
			cursor.move_down(len(buffer.lines))

			line = buffer.current_line(cursor.y)
			cursor.x = min(cursor.x, len(line))