import os
import curses

from syntax.lexer import Lexer
from ui.statusbar import StatusBar
from ui.coordinates import bufferToScreen

class Renderer:
	def __init__(self, stdscr):
		self.stdscr = stdscr

		self.lexer = Lexer()
		self.statusbar = StatusBar()

	def draw(self, editor):
		self.stdscr.erase()
		self.drawBorder()

		if editor.showExplorer:
			self.drawExplorer(editor)
		
		self.drawTabs(editor)

		for paneIndex, pane in enumerate(editor.panes):
			self.drawPane(editor, paneIndex, pane)
		
		self.drawStatusbar(editor)
		if editor.paletteOpen:
			self.drawPalette(editor)
		self.placeCursor(editor)
		self.stdscr.refresh()
	
	def drawBorder(self):
		self.stdscr.border()

	def drawPane(self, editor, paneIndex, pane):
		buffer = editor.buffers[pane.bufferIndex]
		layout = editor.layout
		startX = layout.paneStartX(paneIndex)
		paneWidth = layout.paneWidth()

		visibleLines = buffer.lines[
			pane.scrollY:
			pane.scrollY + layout.paneVisibleHeight()
		]
		if paneIndex > 0:
			for y in range(1, layout.paneVisibleHeight()):
				try:
					self.stdscr.addstr(y, startX - 1, "|")
				except curses.error:
					pass

		for screenY, line in enumerate(visibleLines):
			bufferY = pane.scrollY + screenY

			self.drawLineNumber(editor, startX, screenY, bufferY)
			self.drawTextLine(editor, paneIndex, pane, line, screenY, bufferY, paneWidth)

	def drawLineNumber(self, editor, startX, screenY, bufferY):
		lineNumber = (str(bufferY + 1).rjust(4) + " ")

		try:
			self.stdscr.addstr(screenY + 1, startX, lineNumber, curses.A_DIM)
		except curses.error:
			pass

	def drawTextLine(self, editor, paneIndex, pane, line, screenY, bufferY, paneWidth):
		layout = editor.layout
		x = layout.textStartX(paneIndex)

		tokens = self.lexer.tokenize(line, "python")
		expandedTokens = []

		for token, tokenType in tokens:
			token = token.replace("\t", " " * editor.settings.tabSize)
			expandedTokens.append((token, tokenType))
		tokens = expandedTokens

		lineAttr = 0

		if paneIndex == editor.activePane:
			if bufferY == pane.cursorY:
				lineAttr = editor.theme.get("cursorline")
		for token, tokenType in tokens:
			if x >= (layout.paneStartX(paneIndex) + paneWidth - 1):
				break
			attr = editor.theme.get(tokenType)
			if attr is None:
				attr = editor.theme.get("text")
			try:
				self.stdscr.addstr(
					screenY + 1,
					x,
					token,
					attr | lineAttr
				)
			except curses.error:
				pass
			x += len(token)

	def drawExplorer(self, editor):
		h, _ = self.stdscr.getmaxyx()

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
		try:
			self.stdscr.addstr(
				1,
				2,
				" FILES ",
				curses.A_BOLD
			)
		except curses.error:
			pass

		for i, file in enumerate(editor.explorerFiles):
			if i >= h - 4:
				break

			attr = curses.A_NORMAL
			
			if i == editor.selectedFileIndex:
				attr |= curses.A_REVERSE

			fullPath = os.path.join(
				editor.explorerPath,
				file
			)
			if os.path.isdir(fullPath):
				display = "[+] " + file
			else:
				display = "    " + file
			display = display[:width - 3]
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

		hint = "ENTER Execute | ESC Close"

		self.stdscr.addstr(
			y + height - 2,
			x + 2,
			hint
		)
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

	def drawTabs(self, editor):
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

	def drawStatusbar(self, editor):
		h, w = self.stdscr.getmaxyx()

		self.statusbar.draw(
			self.stdscr,
			editor,
			h,
			w
		)

	def placeCursor(self, editor):
		pane = editor.pane

		screenX, screenY = bufferToScreen(
			editor,
			editor.activePane,
			pane.cursorX,
			pane.cursorY
		)
		try:
			self.stdscr.move(screenY, screenX)
		except curses.error:
			pass