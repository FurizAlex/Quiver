import curses

class StatusBar:
	def draw(self, stdscr, editor, h, w):
		filename = editor.filename or "[NO FILE]"

		status = (
			f" {editor.mode} | "
			f"{filename} | "
			f"Ln {editor.cursor.y + 1} | "
			f"Col {editor.cursor.x + 1} | "
			f"{editor.status}"
		)

		try:
			stdscr.addstr(
				h - 2,
				0,
				status[:w - 1],
				curses.color_pair(5)
			)
		except curses.error:
			pass