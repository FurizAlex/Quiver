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
				buffer.deleteChar(cursor.x, cursor.y)
				cursor.moveLeft()

			elif cursor.y > 0:
				previousLength = len(buffer.lines[cursor.y - 1])

				buffer.mergeLine(cursor.y)

				cursor.y -= 1
				cursor.x = previousLength
		case 10:
			history.push(
				buffer.lines,
				cursor.x,
				cursor.y
			)

			line = buffer.currentLine(cursor.y)
			indent = ""

			for char in line:
				if char in (' ', '\t'):
					indent += char
				else:
					break
			if cursor.x > 0 and line[cursor.x - 1] == '{':
				indent += "    "
			buffer.splitLine(cursor.x, cursor.y)

			buffer.lines[cursor.y + 1] = (
				indent + buffer.lines[cursor.y + 1]
			)
			cursor.y += 1
			cursor.x = len(indent)

		case curses.KEY_LEFT:
			cursor.moveLeft()

		case curses.KEY_RIGHT:
			line = buffer.currentLine(cursor.y)
			cursor.moveRight(len(line))

		case curses.KEY_UP:
			cursor.moveUp()

		case curses.KEY_DOWN:
			cursor.moveDown(len(buffer.lines))

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

					buffer.insertChar(cursor.x, cursor.y, char + closing)
					cursor.x += 1
				else:
					buffer.insertChar(cursor.x, cursor.y, char)
					cursor.x += 1