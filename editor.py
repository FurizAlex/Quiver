import curses

def draw(stdscr, buffer, cursor_x, cursor_y, mode, status, scroll):
	stdscr.clear()
	h, w = stdscr.getmaxyx()

	visible_lines = buffer[scroll:scroll + h - 1]
	for i, line in enumerate(buffer):
		if i < h - 1:
			stdscr.addstr(i, 0, line)

	status_line = f"-- {mode} -- {status} | {cursor_x} : {cursor_y + 1}"
	stdscr.addstr(h - 1, 0, status[:w - 1])

	stdscr.move(cursor_y - scroll, cursor_x)
	stdscr.refresh()

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

def main(stdscr):
	curses.curs_set(1)
	stdscr.keypad(True)
	curses.raw()
	curses.noecho()

	buffer = [""]
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
				case 58:
					mode = "COMMAND"
					command = ""
					status = ":"
				case 105:
					mode = "WRITE"
					status = "-- WRITE --"
				case 113:
					running = False
				case curses.KEY_UP:
					cursor_y = max(0, cursor_y - 1)
				case curses.KEY_DOWN:
					cursor_y = min(len(buffer) - 1, cursor_y + 1)
				case curses.KEY_LEFT:
					cursor_x = max(0, cursor_x - 1)
				case curses.KEY_RIGHT:
					cursor_x = min(len(buffer[cursor_y]), cursor_x + 1)
		
		elif mode == "COMMAND":
			if ch == 10:
				if command.startswith("e "):
					filename = command[2:].strip()
					buffer = openFile(filename)
					cursor_x, cursor_y, scroll = 0, 0, 0
					status = f"Opened: {filename}"

				elif command == "s":
					if filename:
						status = saveFile(filename)
					else:
						status = "Error: No file name"

				elif command == "sq":
					if filename:
						status = saveFile(filename)
					running = False
				elif command == "q":
					running = False
				else:
					status = f"Error: unknown command: {command}"
				mode = "NORMAL"
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