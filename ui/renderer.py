import curses

from syntax.lexer import Lexer
from ui.statusbar import StatusBar

class Renderer:
	def __init__(self, stdscr):
		self.stdscr = stdscr

		self.lexer = Lexer()
		self.statusbar = StatusBar()

	def draw(self, editor):
		self.stdscr.clear()
		self.stdscr.border()

		title = " QUIVER "

		self.stdscr.addstr(
			0,
			2,
			title,
			curses.A_REVERSE
		)

		h, w = self.stdscr.getmaxyx()

		visibleLines = editor.buffer.lines[
			editor.scrollY:
			editor.scrollY + h - 1
		]

		lineNumberWidth = 6

		for screenY, line in enumerate(visibleLines):
			bufferY = screenY + editor.scrollY

			lineNumber = str(bufferY + 1).rjust(4) + " "

			try:
				self.stdscr.addstr(
					screenY + 1,
					1,
					lineNumber,
					curses.A_DIM
				)
			except curses.error:
				pass

			x = lineNumberWidth

			lineAttr = curses.A_REVERSE

			tokens = self.lexer.tokenize(line, "python")

			if bufferY == editor.cursor.y:
				lineAttr = curses.color_pair(5)
			for token, color in tokens:
				if x >= w - 1:
					break
				try:
					self.stdscr.addstr(
						screenY + 1,
						x + 1,
						token,
						curses.color_pair(color) | lineAttr
					)
				except curses.error:
					pass
				x += len(token)
		
		self.statusbar.draw(
			self.stdscr,
			editor,
			h,
			w
		)
		try:
			self.stdscr.move(
				editor.cursor.y - editor.scrollY + 1,
				editor.cursor.x - editor.scrollX + lineNumberWidth + 1
			)
		except curses.error:
			pass
		self.stdscr.refresh()