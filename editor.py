import curses
import re
import os

undo_stack = []
redo_stack = []

def C_hl(line):
	keywords = {
		"int",
		"char",
		"return",
		"if",
		"else",
		"for",
		"while",
		"void",
		"struct",
	}
	return highlightCode(line, keywords)

def Javascript_hl(line):
	keywords = {
		"function",
		"const",
		"let",
		"var",
		"return",
		"if",
		"else",
		"for",
		"while",
	}
	return highlightCode(line, keywords)

def Typescript_hl(line):
	keywords = {
		"function",
		"const",
		"let",
		"var",
		"return",
		"if",
		"else",
		"for",
		"while",
		"int",
		"char",
		"string",
		"bool",
		"void",
	}
	return highlightCode(line, keywords)

def Python_hl(line):
	keywords = {
		"def",
		"if",
		"else",
		"elif",
		"class",
		"import",
		"return",
		"for",
		"while",
		"try",
		"except",
		"with",
		"as",
		"from",
		"pass",
		"in",
		"not",
		"and",
		"or",
	}
	return highlightCode(line, keywords)

def highlightLine(line, filetype):
	match filetype:
		case "python":
			return Python_hl(line)
		case "c":
			return C_hl(line)
		case "javascript":
			return Javascript_hl(line)
		case "typescript":
			return Typescript_hl(line)
		case _:
			return [(line, 4)]

def highlightCode(line):
	tokens = []
	i = 0

	while i < len(line):
		if line[i] == '/' and i + 1 < len(line) and line[i + 1] == '/':
			tokens.append((line[i:], 3))
			break
		elif line[i] in {'"', "'"}:
			quote = line[i]
			j = i + 1
			while j < len(line) and line[j] != quote:
				if line[j] == '\\':
					j += 1
				j += 1
			j = min(j + 1, len(line))
			tokens.append((line[i:j], 2))
			i = j
		else:
			m = re.match(r'\w+', line[i:])
			if m:
				word = m.group(0)
				color = 1 if word in keywords else 4
				tokens.append((word, color))
				i += len(word)
			else:
				tokens.append((line[i], 4))
				i += 1
	return tokens

def draw(stdscr, buffer, cursor_x, cursor_y, mode, status, scroll, filetype):
	stdscr.clear()
	h, w = stdscr.getmaxyx()

	for i, line in enumerate(buffer):
		if i < h - 1:
			x = 0
			for token, color in highlightLine(line, filetype):
				stdscr.addstr(i, x, token, curses.color_pair(color))
				x += len(token)

	if mode == "COMMAND":
		status = status
	else:
		status_line = f"-- {mode} -- {status} | {cursor_x} : {cursor_y + 1}"
	stdscr.addstr(h - 1, 0, status[:w - 1])

	stdscr.move(cursor_y - scroll, cursor_x)
	stdscr.refresh()

def get_key(stdscr):
    ch = stdscr.getch()

    if ch == 27:
        stdscr.nodelay(True)
        next1 = stdscr.getch()
        next2 = stdscr.getch()
        next3 = stdscr.getch()
        stdscr.nodelay(False)

        seq = (next1, next2, next3)

        if seq == (91, 49, 59):
            fourth = stdscr.getch()
            if fourth == 68:
                return "CTRL_LEFT"
            elif fourth == 67:
                return "CTRL_RIGHT"
        return "ESC"
    else:
        return ch

def getFileType(filename):
	if not filename:
		return "plain"
	elif filename.endswith(".py"):
		return "python"
	elif filename.endswith(".c") or filename.endswith(".h"):
		return "c"
	elif filename.endswith(".cpp") or filename.endswith(".hpp"):
		return "c++"
	elif filename.endswith(".js"):
		return "javascript"
	elif filename.endswith(".rs"):
		return "rust"
	elif filename.endswith(".pyx"):
		return "pyxis"
	elif filename.endswith(".apch") or filename.endswith(".aphh"):
		return "apache"
	elif filename.endswith(".tsx") or filename.endswith(".ts"):
		return "typescript"
	else:
		return "plain"

def openFile(filename):
	if not os.path.exists(filename):
		return [""]
	try:
		with open(filename, 'r') as f:
			return f.read().splitlines()
	except Exception as e:
		return [f"Error: Opening file: {e}"]

def saveFile(filename, buffer):
	try:
		with open(filename, 'w') as f:
			f.write('\n'.join(buffer))
		return f"Saved {filename}"
	except Exception as e:
		return f"Error: Saving file: {e}"

def nextWordStart(line, pos):
	match = re.search(r'\w\w*', line[pos + 1:])
	return pos + 1 + match.start() if match else len(line)

def nextWordEnd(line, pos):
	match = re.search(r'\w\w*', line[pos + 1:])
	if match:
		return pos + 1 + match.start() + len(match.group())
	return len(line)

def prevWordStart(line, pos):
	for i in range(pos - 1, -1, -1):
		if re.match(r'\w', line[i]) and (i == 0 or not re.match(r'\w', line[i - 1])):
			return i
	return 0

def main(stdscr):
	curses.curs_set(1)
	stdscr.keypad(True)
	curses.raw()
	curses.noecho()
	curses.start_color()
	curses.use_default_colors()
	curses.init_pair(1, curses.COLOR_CYAN, -1)
	curses.init_pair(2, curses.COLOR_GREEN, -1)
	curses.init_pair(3, curses.COLOR_YELLOW, -1)
	curses.init_pair(4, curses.COLOR_WHITE, -1)

	TAB_WIDTH = 4

	gBuffer = ""
	buffer = [""]
	bookmarks = {}
	cursor_x, cursor_y = 0, 0
	mode = "NORMAL"
	scroll = 0
	status = "-- Welcome to Quiver --"
	tab_spaces = " " * TAB_WIDTH
	running = True
	filename = None
	command = ""
	filetype = getFileType(filename)

	def saveUndoState():
		undo_stack.append((buffer.copy(), cursor_x, cursor_y))
		if len(undo_stack) > 100:
			undo_stack.pop(0)

	def undo():
		if undo_stack:
			redo_stack.append((buffer.copy(), cursor_x, cursor_y))
			state = undo_stack.pop()
			restoreState(*state)

	def redo():
		if redo_stack:
			undo_stack.append((buffer.copy, cursor_x, cursor_y))
			start = redo_stack.pop()
			restoreState(*state)

	def pushUndo():
		undo_stack.append((buffer.copy(), cursor_x, cursor_y))
		redo_stack.clear()

	def restoreState(savedBuffer, x, y):
		nonlocal buffer, cursor_x, cursor_y
		buffer = savedBuffer.copy()
		cursor_x = x
		cursor_y = y

	while running:
		h, w = stdscr.getmaxyx()
		if cursor_y < scroll:
			scroll = cursor_y
		elif cursor_y >= scroll + h - 1:
			scroll = cursor_y - (h - 2)

		draw(stdscr, buffer, cursor_x, cursor_y, mode, status, scroll, filetype)
		ch = stdscr.getch()

		if mode == "NORMAL":
			match ch:
				case 27:
					running = False
				case 58:
					mode = "COMMAND"
					command = ""
					status = ":"
				case 105:
					mode = "EDIT"
					status = "-- EDIT --"

				case 119:
					pushUndo()
					line = buffer[cursor_y]
					cursor_x = nextWordStart(line, cursor_x)
					gBuffer = ""
				case 101:
					pushUndo()
					line = buffer[cursor_y]
					cursor_x = nextWordEnd(line, cursor_x)
					gBuffer = ""
				case 98:
					pushUndo()
					line = buffer[cursor_y]
					cursor_x = prevWordStart(line, cursor_x)
					gBuffer = ""

				case 109:
					pushUndo()
					stdscr.addstr(h - 1, 0, "Bookmark: ")
					stdscr.refresh()
					mark = stdscr.getch()
					bookmarks[chr(mark)] = (cursor_y, cursor_x)
				case 39:
					pushUndo()
					mark = stdscr.getch()
					key = chr(mark)
					if key in bookmarks:
						cursor_y, cursor_x = bookmarks[key]

				case 153:
					pushUndo()
					cursor_y = max(0, cursor_y - 1)
					cursor_x = min(cursor_x, len(buffer[cursor_y]))
					gBuffer = ""
				case 152:
					pushUndo()
					cursor_y = min(len(buffer) - 1, cursor_y + 1)
					cursor_x = min(cursor_x, len(buffer[cursor_y]))
					gBuffer = ""
				case 150:
					pushUndo()
					cursor_x = max(0, cursor_x - 1)
					gBuffer = ""
				case 154:
					pushUndo()
					cursor_x = min(len(buffer[cursor_y]), cursor_x + 1)
					gBuffer = ""
				case 48:
					pushUndo()
					cursor_x = 0
					gBuffer = ""
				case 94:
					pushUndo()
					line = buffer[cursor_y]
					cursor_x = len(line) - len(line.lstrip())
					gBuffer = ""
				case 36:
					pushUndo()
					cursor_x = len(buffer[cursor_y])
					gBuffer = ""
				case 71:
					pushUndo()
					cursor_y = len(buffer) - 1
					cursor_x = min(cursor_x, len(buffer[cursor_y]))
					gBuffer = ""
				case 103:
					pushUndo()
					if gBuffer == 'g':
						cursor_y = 0
						cursor_x = min(cursor_x, len(buffer[0]))
						gBuffer = ""
					else:
						gBuffer = 'g'

				case 9:
					pushUndo()
					line = buffer[cursor_y]
					buffer[cursor_y] = line[:cursor_x] + tab_spaces + line[cursor_x:]
					cursor_x += len(tab_spaces)
					gBuffer = ""

				case 4:
					pushUndo()
					cursor_y = min(len(buffer) - 1, cursor_y + h // 2)
					gBuffer = ""
				case 21:
					pushUndo()
					cursor_y = max(0, cursor_y - h // 2)
					gBuffer = ""

				case curses.KEY_UP:
					pushUndo()
					cursor_y = max(0, cursor_y - 1)
					cursor_x = min(cursor_x, len(buffer[cursor_y]))
					gBuffer = ""
				case curses.KEY_DOWN:
					pushUndo()
					cursor_y = min(len(buffer) - 1, cursor_y + 1)
					cursor_x = min(cursor_x, len(buffer[cursor_y]))
					gBuffer = ""
				case curses.KEY_LEFT:
					pushUndo()
					cursor_x = max(0, cursor_x - 1)
					gBuffer = ""
				case curses.KEY_RIGHT:
					pushUndo()
					cursor_x = min(len(buffer[cursor_y]), cursor_x + 1)
					gBuffer = ""
				case _:
					gBuffer = ""
		
		elif mode == "COMMAND":
			if ch == 10:
				if command.isdigit():
					line_num = int(command)
					if 1 <= line_num <= len(buffer):
						cursor_y = line_num - 1
						cursor_x = min(cursor_x, len(buffer[cursor_y]))
				elif command.startswith("open "):
					filename = command[2:].strip()
					buffer = openFile(filename)
					cursor_x, cursor_y, scroll = 0, 0, 0
					status = f"Opened: {filename}"

				elif command == "s":
					if filename:
						status = saveFile(filename, buffer)
					else:
						status = "Error: No file name"

				elif command == "sq":
					if filename:
						status = saveFile(filename, buffer)
					running = False
				elif command == "q":
					running = False
				else:
					status = f"Error: unknown command: {command}"
				mode = "NORMAL"
				status = ""

			elif ch == 27:
				mode = "NORMAL"
				status = ""
			elif ch == curses.KEY_BACKSPACE or ch == 127:
				command = command[:-1]
				status = ":" + command
			elif 32 <= ch <= 126:
				command += chr(ch)
				status = ":" + command

		elif mode == "EDIT":
			match ch:
				case 27:
					mode = "NORMAL"
					status = ""
				case curses.KEY_BACKSPACE:
					pushUndo()
					line = buffer[cursor_y]

					if cursor_x > 0:
						buffer[cursor_y] = line[:cursor_x - 1] + line[cursor_x:]
						cursor_x -= 1
					elif cursor_y > 0:
						prev = buffer[cursor_y - 1]
						cursor_x = len(prev)
						buffer[cursor_y - 1] = prev + buffer[cursor_y]
						buffer.pop(cursor_y)
						cursor_y -= 1
				case 127: #Enter
					pushUndo()
					line = buffer[cursor_y]

					if cursor_x > 0:
						buffer[cursor_y] = line[:cursor_x - 1] + line[cursor_x:]
						cursor_x -= 1
					elif cursor_y > 0:
						prev = buffer[cursor_y - 1]
						cursor_x = len(prev)
						buffer[cursor_y - 1] = prev + buffer[cursor_y]
						buffer.pop(cursor_y)
						cursor_y -= 1
				case 10:
					pushUndo()
					line = buffer[cursor_y]
					indent = re.match(r'^\s*', line).group(0)
					buffer[cursor_y] = line[:cursor_x]
					buffer.insert(cursor_y + 1, indent + line[cursor_x:])
					cursor_y += 1
					cursor_x = len(indent)

				case 9:
					pushUndo()
					line = buffer[cursor_y]
					buffer[cursor_y] = line[:cursor_x] + tab_spaces + line[cursor_x:]
					cursor_x += len(tab_spaces)

				case 26: #Undo
					if undo_stack:
						redo_stack.append((buffer.copy(), cursor_x, cursor_y))
						buffer, cursor_x, cursor_y = undo_stack.pop()
				case 25: #Redo
					if redo_stack:
						undo_stack.append((buffer.copy(), cursor_x, cursor_y))
						buffer, cursor_x, cursor_y = redo_stack.pop()

				case curses.KEY_UP:
					pushUndo()
					cursor_y = max(0, cursor_y - 1)
				case curses.KEY_DOWN:
					pushUndo()
					cursor_y = min(len(buffer) - 1, cursor_y + 1)
				case curses.KEY_LEFT:
					pushUndo()
					cursor_x = max(0, cursor_x - 1)
				case curses.KEY_RIGHT:
					pushUndo()
					cursor_x = min(len(buffer[cursor_y]), cursor_x + 1)

			if 32 <= ch <= 126:
				pushUndo()
				char = chr(ch)
				pairs = {'{': '}', '(': ')', '[': ']', '"': '"', "'": "'"}

				if char in pairs:
					line = buffer[cursor_y]
					closing = pairs[char]
					buffer[cursor_y] = line[:cursor_x] + char + closing + line[cursor_x:]
					cursor_x += 1
				else:
					line = buffer[cursor_y]
					buffer[cursor_y] = line[:cursor_x] + char + line[cursor_x:]
					cursor_x += 1
			
			cursor_y = max(0, min(len(buffer) - 1, cursor_y))
		
		cursor_x = max(0, min(len(buffer[cursor_y]), cursor_x))

if __name__ == "__main__":
	curses.wrapper(main)