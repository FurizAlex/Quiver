import curses

class Rendeder:
	def __init__(self, stdscr):
		self.stdscr = stdscr

	def draw(self, editor):
		self.stdscr.clear()

		h, w = self.stdscr.getmaxyx()

		visible = editor.buffer.lines[
			editor.scrollY:
			editor.scrollY + h - 1
		]

		for screen_y, line in enumerate(visible):
			x = 0
			tokens = self.lexer.tokenize(line, "python")

			for token, color in tokens:
				if x >= w - 1:
					break
				try:
					self.stdscr.addstr(
						screen_y,
						x,
						0,
						line[:w - 1]
					)
				except Curses.error:
					pass
				x += len(token)
		
		status = (
			f"{editor.mode} | "
			f"(editor.cursor.x):{editor.cursor.y}"
		)
		try:
			self.stdscr.addstr(
				h - 1,
				0,
				status[:w - 1],
				curses.A_REVERSE
			)
		except curses.error:
			pass
		try:
			self.stdscr.move(
				editor.cursor.y - editor.scrollY,
				editor.cursor.x
			)
		except curses.error:
			pass
		self.stdscr.refresh()