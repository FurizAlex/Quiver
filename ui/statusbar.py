import curses

class StatusBar:
	def draw(self, stdscr, editor, h, w):
		filename = editor.filename or "[NO FILE]"

		if editor.saving:
			left = (
				f" SAVE AS: {editor.saveInput}"
			)
		else:
			left = (
				f" {editor.mode} | "
				f"{filename} | "
				f"Ln {editor.pane.cursorY + 1} | "
				f"Col {editor.pane.cursorX + 1} | "
				f"{editor.buffer.language.upper()} | "
				f"{editor.status}"
			)

		right = (
			"^S Save  "
			"^O Open  "
			"^P Commands  "
			"^N Next"
		)

		available = w - len(right) - 1
		if len(left) > available:
			left = left[:available]

		space = max(1, w - len(left) - len(right) - 1)

		status = (left + (" ") * space + right)

		try:
			stdscr.addstr(
				h - 2,
				0,
				status[:w - 1],
				editor.theme.get("statusBar")
			)
		except curses.error:
			pass