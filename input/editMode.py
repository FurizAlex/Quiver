import curses

PAIRS = {
	'(': ')',
	'[': ']',
	'{': '}',
	'"': '"',
	"'": "'"
}

def handle(editor, key):
	cursor = editor.cursor
	buffer = editor.buffer
	history = editor.history

	match key:
		case 27:
			editor.mode = "NORMAL"
			editor.status = "NORMAL MODE"

		case curses.KEY_BACKSPACE | 127:
			history.push(
				buffer.lines,
				cursor.x,
				cursor.y
			)

			if cursor.x > 0:
				buffer.delete_char(cursor.x, cursor.y)
				cursor.move_left()

			elif cursor.y > 0:
				previous_length = len(buffer.lines[cursor.y - 1])

				buffer.merge_line(cursor.y)

				cursor.y -= 1
				cursor.x = previous_length
		case 10:
			history.push(
				buffer.lines,
				cursor.x,
				cursor.y
			)

			buffer.split_line(cursor.x, cursor.y)

			cursor.y += 1
			cursor.x = 0

		case curses.KEY_LEFT:
			cursor.move_left()

		case curses.KEY_RIGHT:
			line = buffer.current_line(cursor.y)
			cursor.move_right(len(line))

		case curses.KEY_UP:
			cursor.move_up()

		case curses.KEY_DOWN:
			cursor.move_down(len(buffer.lines))

		case 26:
			current_state = (
				buffer.lines.copy(),
				cursor.x,
				cursor.y
				)

			state = history.undo(current_state)

			buffer.lines = state[0].copy()
			cursor.x = state[1]
			cursor.y = state[2]

		case 25:
			current_state = (
				buffer.lines.copy(),
				cursor.x,
				cursor.y
			)
			state = history.redo(current_state)

			buffer.lines = state[0].copy()
			cursor.x = state[1]
			cursor.y = state[2]

		case _:
			if 32 <= key <= 126:
				history.push(
					buffer.lines,
					cursor.x,
					cursor.y
				)
				char = chr(key)

				if char in PAIRS:
					closing = PAIRS[char]

					buffer.insert_char(cursor.x, cursor.y, char + closing)
					cursor.x += 1
				else:
					buffer.insert_char(cursor.x, cursor.y, char)
					cursor.x += 1