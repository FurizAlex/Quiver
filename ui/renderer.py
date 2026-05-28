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

		h, w = self.stdscr.getmaxyx()

		if editor.showExplorer:
			self.drawExplorer(editor, h)

		self.drawTabs(editor, w)

		paneCount = len(editor.panes)
		usableWidth = w - 2

		if editor.showExplorer:
			usableWidth -= editor.explorerWidth + 1
		paneWidth = usableWidth // paneCount

		for paneIndex, pane in enumerate(editor.panes):
			buffer = editor.buffers[pane.bufferIndex]
			startX = 1

			if editor.showExplorer:
				startX += editor.explorerWidth + 1
			startX += paneIndex * paneWidth

			if paneIndex > 0:
				for y in range(1, h - 1):
					try:
						self.stdscr.addstr(
							y,
							startX - 1,
							"|"
						)
					except curses.error:
						pass

			visibleLines = buffer.lines[
				pane.scrollY:
				pane.scrollY + h - 2
			]
			lineNumberWidth = 6

			for screenY, line in enumerate(visibleLines):
				bufferY = screenY + editor.scrollY

				lineNumber = str(bufferY + 1).rjust(4) + " "

				try:
					self.stdscr.addstr(
						screenY + 1,
						startX,
						lineNumber,
						curses.A_DIM
					)
				except curses.error:
					pass

				x = startX + lineNumberWidth
				tokens = self.lexer.tokenize(line, "python")
				lineAttr = curses.A_NORMAL

				if paneIndex == editor.activePane:
					if bufferY == pane.cursorY:
						lineAttr = curses.color_pair(5)
				for token, color in tokens:
					if x >= w - 1:
						break
					try:
						self.stdscr.addstr(
							screenY + 1,
							x,
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

		activePane = editor.pane
		cursorStartX = 1

		if editor.showExplorer:
			cursorStartX += editor.explorerWidth + 1
		cursorStartX += (
			editor.activePane * paneWidth
		)
		try:
			self.stdscr.move(
				activePane.cursorY - activePane.scrollY + 1,
				activePane.cursorX + lineNumberWidth + cursorStartX
			)
		except curses.error:
			pass
		if editor.paletteOpen:
			self.drawPalette(editor, h, w)
		self.stdscr.refresh()

	def drawExplorer(self, editor, h):
		width = editor.explorerWidth

		for y in range(1, h - 1):
			try:
				self.stdscr.addstr(
					y,
					width,
					"|"
				)
			except curses.error:
				pass
		title = " FILES "

		try:
			self.stdscr.addstr(
				1,
				2,
				title,
				curses.A_BOLD
			)
		except curses.error:
			pass

		for i, file in enumerate(editor.explorerFiles):
			if i >= h - 4:
				break

			attr = curses.A_NORMAL

			if i == editor.selectedFileIndex:
				attr = curses.A_REVERSE

			display = file[:width - 3]
			try:
				self.stdscr.addstr(
					i + 3,
					2,
					display.ljust(width - 3),
					attr
				)
			except curses.error:
				pass
	
	def drawPalette(self, editor, h, w):
		width = 40
		height = 10

		x = (w - width) // 2
		y = (h - height) // 2

		for py in range(height):
			for px in range(width):
				char = " "

				if py == 0 or py == height - 1:
					char = "-"
				if px == 0 or px == width - 1:
					char = "|"
				if py == 0 and px == 0:
					char = "┌"
				if py == 0  and px == width - 1:
					char = "┐"
				if py == height - 1 and px == 0:
					char = "└"
				if py == height - 1 and px == width - 1:
					char = "┘"

				try:
					self.stdscr.addstr(
						y + py,
						x + px,
						char
					)
				except curses.error:
					pass
		
		title = " COMMAND PALETTE "

		try:
			self.stdscr.addstr(
				y,
				x + 2,
				title,
				curses.A_BOLD
			)
		except curses.error:
			pass

		query = "> " + editor.paletteInput

		try:
			self.stdscr.addstr(
				y + 2,
				x + 2,
				query
			)
		except curses.error:
			pass

		items = [
			item for item in editor.paletteItems
			if editor.paletteInput.lower()
			in item.lower()
		]

		for i, item in enumerate(items[:5]):
			attr = curses.A_NORMAL

			if i == editor.paletteSelection:
				attr = curses.A_REVERSE

			try:
				self.stdscr.addstr(
					y + 4 + i,
					x + 2,
					item,
					attr
				)
			except curses.error:
				pass

	def drawTabs(self, editor, w):
		x = 2

		for i, buffer in enumerate(editor.buffers):
			title = f" {buffer.name} "

			if buffer.modified:
				title += "* "

			attr = curses.A_NORMAL

			if i == editor.currentBuffer:
				attr = curses.A_REVERSE
			
			try:
				self.stdscr.addstr(
					0,
					x,
					title,
					attr
				)
			except curses.error:
				pass
			x += len(title) + 1