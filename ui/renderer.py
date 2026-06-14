import os
import curses

from syntax.lexer import Lexer
from ui.statusbar import StatusBar
from ui.coordinates import bufferToScreen
from ui.rendererBase import RendererBase

class Renderer(RendererBase):
	def __init__(self, stdscr):
		self.stdscr = stdscr

		self.lexer = Lexer()
		self.statusbar = StatusBar()

	def draw(self, editor):
		self.clear()
		self.drawBorder()

		if editor.showExplorer:
			self.drawExplorer(editor)
		
		self.drawTabs(editor)

		for paneIndex, pane in enumerate(editor.panes):
			self.drawPane(editor, paneIndex, pane)
		
		self.drawStatusbar(editor)
		if editor.completionActive and editor.completions:
			self.drawCompletion(editor)
		if editor.paletteOpen:
			self.drawPalette(editor)
		if editor.searchMode:
			self.drawSearch(editor)
		self.placeCursor(editor)
		self.present()

	def clear(self):
		self.stdscr.erase()

	def present(self):
		self.stdscr.refresh()

	def drawText(self, x, y, text, style=0):
		self.safeAddstr(y, x, text, style)

	def drawLineNumber(self, x1, y1, x2, y2, style=0):
		if x1 == x2:
			for y in range(y1, y2 + 1):
				self.safeAddstr(y, x1, "|", style)
		elif y1 == y2:
			length = (x2 - x1) + 1
			self.safeAddstr(
				y1,
				x1,
				"-" * length,
				style
			)
	
	def drawBorder(self):
		self.stdscr.border()

	def drawPane(self, editor, paneIndex, pane):
		buffer = pane.buffer
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
					attr = editor.theme.get("splitter")

					if paneIndex == editor.activePane:
						attr = editor.theme.get("activeSplitter")
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
		pane = editor.panes[editor.activePane]
		lineNumber = (str(bufferY + 1).rjust(4) + " ")
		diagnostics = editor.pane.buffer.diagnostics.atLine(bufferY)
		attr = editor.theme.get("lineNumber")

		if diagnostics:
			attr = editor.theme.get("diagnosticError")
		if bufferY == pane.cursorY:
			attr = editor.theme.get("currentLineNumber")
		try:
			self.safeAddstr(screenY + 1, startX, lineNumber, attr)
		except curses.error:
			pass

	def drawTextLine(self, editor, paneIndex, pane, line, screenY, bufferY, paneWidth):
		layout = editor.layout
		startX = layout.textStartX(paneIndex)
		buffer = pane.buffer
		
		tokens = self.lexer.tokenize(line, buffer.language)
		x = startX
		bufferX = 0
		visualX = 0

		for tokenText, tokenType in tokens:
			for ch in tokenText:
				if bufferX < pane.scrollX:
					bufferX += 1
					continue

				attr = editor.theme.get(tokenType)
				if editor.selection.contains(bufferX, bufferY):
					attr = editor.theme.get("selection")

				if ch == "\t":
					spaces = editor.settings.tabSize - (visualX % editor.settings.tabSize)
					self.safeAddstr(screenY + 1, startX + visualX, " " * spaces, attr)
					visualX += spaces
					bufferX += 1
				else:
					self.safeAddstr(screenY + 1, startX + visualX, ch, attr)
					visualX += 1
					bufferX += 1
		while x < startX + paneWidth:
			if editor.selection.contains(bufferX, bufferY):
				self.safeAddstr(screenY, x, " ", editor.theme.get("selection"))
			x += 1
			bufferX += 1

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
				editor.theme.get("explorerTitle")
			)
		except curses.error:
			pass

		for i, file in enumerate(editor.explorerFiles):
			if i >= h - 4:
				break

			attr = editor.theme.get("explorerItem")
			
			if i == editor.selectedFileIndex:
				attr = editor.theme.get("explorerSelection")

			fullPath = os.path.join(
				editor.explorerPath,
				file
			)
			if os.path.isdir(fullPath):
				display = "> " + file
			else:
				display = "- " + file
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
		h, w = self.stdscr.getmaxyx()
		width = 40
		height = min(len(editor.paletteItems) + 7, h - 4)

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
						char,
						editor.theme.get("paletteBorder")
					)
				except curses.error:
					pass
		
		title = " COMMAND PALETTE "

		try:
			self.safeAddstr(
				y,
				x + 2,
				title,
				editor.theme.get("paletteTitle")
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
		from input.paletteMode import filtered
		maxItems = height - 6
		items = filtered(editor)
		items = items[:maxItems]

		for i, item in enumerate(items):
			attr = editor.theme.get("paletteItem")

			if i == editor.paletteSelection:
				attr = editor.theme.get("paletteSelection")

			try:
				self.safeAddstr(
					y + 4 + i,
					x + 2,
					item["name"],
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

			attr = editor.theme.get("tab")

			if i == editor.currentBuffer:
				attr = editor.theme.get("activeTab")
			
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

	def drawCompletion(self, editor):
		h, w = self.stdscr.getmaxyx()
		pane = editor.pane

		from ui.coordinates import bufferToScreen
		screenX, screenY = bufferToScreen(editor, editor.activePane, pane.cursorX, pane.cursorY)
		completions = editor.completions
		boxWidth = max(len(c) for c in completions) + 4
		boxHeight = len(completions)

		boxX = screenX
		boxY = screenY + 1
		if boxX + boxWidth >= w:
			boxX = w - boxWidth - 1
		if boxY + boxHeight >= h - 2:
			boxY = screenY - boxHeight
		for i, word in enumerate(completions):
			if boxY + i < 1 or boxY + i >= h - 2:
				continue
			if i == editor.completionIndex:
				attr = editor.theme.get("paletteSelection")
			else:
				attr = editor.theme.get("paletteItem")
			display = f" {word:<{boxWidth - 2}} "
			self.safeAddstr(boxY + i, boxX, display[:boxWidth], attr)

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

	def drawSearch(self, editor):
		h, w = self.stdscr.getmaxyx()
		text = f"Search: {editor.searchInput}"

		self.safeAddstr(
			h - 3,
			2,
			text,
			editor.theme.get("searchBar")
		)