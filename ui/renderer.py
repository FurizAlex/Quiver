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
					attr = curses.A_DIM

					if paneIndex == editor.activePane:
						attr = curses.A_BOLD
					self.safeAddstr(
						y,
						startX - 1,
						"|",
						attr
					)
				except curses.error:
					pass

		for screenY, line in enumerate(visibleLines):
			bufferY = pane.scrollY + screenY

			self.drawLineNumber(editor, startX, screenY, bufferY)
			self.drawTextLine(editor, paneIndex, pane, line, screenY, bufferY, paneWidth)

	def drawLineNumber(self, editor, startX, screenY, bufferY):
		lineNumber = (str(bufferY + 1).rjust(4) + " ")

		try:
			self.safeAddstr(screenY + 1, startX, lineNumber, curses.A_DIM)
		except curses.error:
			pass

	def drawTextLine(self, editor, paneIndex, pane, line, screenY, bufferY, paneWidth):
		layout = editor.layout
		startX = layout.textStartX(paneIndex)
		tokens = self.lexer.tokenize(line, "python")
		expandedTokens = []
		x = startX

		for token, tokenType in tokens:
			expanded = ""
			for ch in token:
				if ch == "\t":
					tabSize = editor.settings.tabSize
					spaces = (tabSize - ((x - startX) % tabSize))
					expanded += (" " * spaces)
				else:
					expanded += ch
			token = expanded
			expandedTokens.append((token, tokenType))

		fullLine = "".join(token for token, _ in expandedTokens)

		if pane.scrollX > 0:
			fullLine = fullLine[pane.scrollX:]
		tokens = self.lexer.tokenize(fullLine, "python")
		expandedTokens = []
		for token, tokenType in tokens:
			expanded = ""
			for ch in token:
				if ch == "\t":
					tabSize = editor.settings.tabSize
					spaces = (tabSize - ((x - startX) % tabSize))
					expanded += (" " * spaces)
				else:
					expanded += ch
			token = expanded
			expandedTokens.append((token, tokenType))
		lineAttr = 0

		if paneIndex == editor.activePane:
			if bufferY == pane.cursorY:
				lineAttr = editor.theme.get("cursorline")
		for token, tokenType in expandedTokens:
			attr = editor.theme.get(tokenType)

			if attr is None:
				attr = editor.theme.get("text")
			for charIndex, char in enumerate(token):
				if x >= (layout.paneStartX(paneIndex) + paneWidth - 1):
					return
				finalAttr = attr | lineAttr

				bufferX = ((x - startX) + pane.scrollX)

				if editor.selection.contains(bufferX, bufferY):
					finalAttr = (editor.theme.get("selection") | lineAttr)
				try:
					self.safeAddstr(
						screenY + 1,
						x,
						char,
						finalAttr
					)
				except curses.error:
					pass
				x += 1

	def drawExplorer(self, editor):
		h, _ = self.stdscr.getmaxyx()

		width = editor.explorerWidth

		for y in range(1, h - 1):
			try:
				self.safeAddstr(
					y,
					width,
					"|"
				)
			except curses.error:
				pass
		try:
			self.safeAddstr(
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
				self.safeAddstr(
					i + 3,
					2,
					display.ljust(width - 3),
					attr
				)
			except curses.error:
				pass
	
	def drawPalette(self, editor):
		width = 40
		height = 10
		h, w = self.stdscr.getmaxyx()

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
					self.safeAddstr(
						y + py,
						x + px,
						char
					)
				except curses.error:
					pass
		
		title = " COMMAND PALETTE "

		try:
			self.safeAddstr(
				y,
				x + 2,
				title,
				curses.A_BOLD
			)
		except curses.error:
			pass

		query = "> " + editor.paletteInput

		hint = "ENTER Execute | ESC Close"

		self.safeAddstr(
			y + height - 2,
			x + 2,
			hint
		)
		try:
			self.safeAddstr(
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
				self.safeAddstr(
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
				self.safeAddstr(
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
		h, w = self.stdscr.getmaxyx()

		screenX, screenY = bufferToScreen(
			editor,
			editor.activePane,
			pane.cursorX,
			pane.cursorY
		)
		if (0 <= screenY < h and 0 <= screenX < w):
			try:
				self.stdscr.move(screenY, screenX)
			except curses.error:
				pass

	def safeAddstr(self, y, x, text, attr=0):
		h, w = self.stdscr.getmaxyx()

		if y < 0 or y >= h:
			return
		if x < 0 or x >= w:
			return
		if x + len(text) >= w:
			text = text[:w - x - 1]
		
		if not text:
			return
		try:
			self.stdscr.addstr(
				y,
				x,
				text,
				attr
			)
		except curses.error:
			pass