import curses
import re

def draw(stdscr, buffer, cursor_x, cursor_y, mode, status, scroll):
	stdscr.clear()
	h, w = stdscr.getmaxyx()

	visible_lines = buffer[scroll:scroll + h - 1]
	for i, line in enumerate(buffer):
		if i < h - 1:
			stdscr.addstr(i, 0, line)

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

def openFile(filename):
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

	gBuffer = ""
	buffer = [""]
	bookmarks = {}
	cursor_x, cursor_y = 0, 0
	mode = "NORMAL"
	scroll = 0
	status = "-- Welcome to Quiver --"
	running = True
	filename = None
	command = ""
	
	while running:
		h, w = stdscr.getmaxyx()
		if cursor_y < scroll:
			scroll = cursor_y
		elif cursor_y >= scroll + h - 1:
			scroll = cursor_y - (h - 2)

		draw(stdscr, buffer, cursor_x, cursor_y, mode, status, scroll)
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
					mode = "WRITE"
					status = "-- WRITE --"

				case 119:
					line = buffer[cursor_y]
					cursor_x = nextWordStart(line, cursor_x)
					gBuffer = ""
				case 101:
					line = buffer[cursor_y]
					cursor_x = nextWordEnd(line, cursor_x)
					gBuffer = ""
				case 98:
					line = buffer[cursor_y]
					cursor_x = prevWordStart(line, cursor_x)
					gBuffer = ""

				case 109:
					stdscr.addstr(h - 1, 0, "Bookmark: ")
					stdscr.refresh()
					mark = stdscr.getch()
					bookmarks[chr(mark)] = (cursor_y, cursor_x)
				case 39:
					mark = stdscr.getch()
					key = chr(mark)
					if key in bookmarks:
						cursor_y, cursor_x = bookmarks[key]

				case 153:
					cursor_y = max(0, cursor_y - 1)
					cursor_x = min(cursor_x, len(buffer[cursor_y]))
					gBuffer = ""
				case 152:
					cursor_y = min(len(buffer) - 1, cursor_y + 1)
					cursor_x = min(cursor_x, len(buffer[cursor_y]))
					gBuffer = ""
				case 150:
					cursor_x = max(0, cursor_x - 1)
					gBuffer = ""
				case 154:
					cursor_x = min(len(buffer[cursor_y]), cursor_x + 1)
					gBuffer = ""
				case 48:
					cursor_x = 0
					gBuffer = ""
				case 94:
					line = buffer[cursor_y]
					cursor_x = len(line) - len(line.lstrip())
					gBuffer = ""
				case 36:
					cursor_x = len(buffer[cursor_y])
					gBuffer = ""
				case 71:
					cursor_y = len(buffer) - 1
					cursor_x = min(cursor_x, len(buffer[cursor_y]))
					gBuffer = ""
				case 103:
					if gBuffer == 'g':
						cursor_y = 0
						cursor_x = min(cursor_x, len(buffer[0]))
						gBuffer = ""
					else:
						gBuffer = 'g'

				case 4:
					cursor_y = min(len(buffer) - 1, cursor_y + h // 2)
				case 21:
					cursor_y = max(0, cursor_y - h // 2)

				case curses.KEY_UP:
					cursor_y = max(0, cursor_y - 1)
					cursor_x = min(cursor_x, len(buffer[cursor_y]))
					gBuffer = ""
				case curses.KEY_DOWN:
					cursor_y = min(len(buffer) - 1, cursor_y + 1)
					cursor_x = min(cursor_x, len(buffer[cursor_y]))
					gBuffer = ""
				case curses.KEY_LEFT:
					cursor_x = max(0, cursor_x - 1)
					gBuffer = ""
				case curses.KEY_RIGHT:
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

		elif mode == "WRITE":
			match ch:
				case 27:
					mode = "NORMAL"
					status = ""
				case curses.KEY_BACKSPACE:
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
				case 127:
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
					line = buffer[cursor_y]
					buffer[cursor_y] = line[:cursor_x]
					buffer.insert(cursor_y + 1, line[cursor_x:])
					cursor_y += 1
					cursor_x = 0

				case curses.KEY_UP:
					cursor_y = max(0, cursor_y - 1)
				case curses.KEY_DOWN:
					cursor_y = min(len(buffer) - 1, cursor_y + 1)
				case curses.KEY_LEFT:
					cursor_x = max(0, cursor_x - 1)
				case curses.KEY_RIGHT:
					cursor_x = min(len(buffer[cursor_y]), cursor_x + 1)

			if 32 <= ch <= 126:
				line = buffer[cursor_y]
				buffer[cursor_y] = line[:cursor_x] + chr(ch) + line[cursor_x:]
				cursor_x += 1
			
			cursor_y = max(0, min(len(buffer) - 1, cursor_y))
		
		cursor_x = max(0, min(len(buffer[cursor_y]), cursor_x))

if __name__ == "__main__":
	curses.wrapper(main)