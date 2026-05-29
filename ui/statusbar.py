import curses

class StatusBar:
	def draw(self, stdscr, editor, h, w):
		filename = editor.filename or "[NO FILE]"

		status = (
			f" {editor.mode} | "
			f"{filename} | "
			f"Ln {editor.pane.cursorY + 1} | "
			f"Col {editor.pane.cursorX + 1} | "
			f"{editor.status}"
		)

		try:
			stdscr.addstr(
				h - 2,
				0,
				status[:w - 1],
				editor.theme.get("statusBar")
			)
		except curses.error:
			pass