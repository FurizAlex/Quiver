from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFontMetrics
from PyQt6.QtCore import Qt
import os

from frontend.qt.amigaPalette import getColor

class OverlayWidget(QWidget):
	def __init__(self, editor, font, parent=None):
		super().__init__(parent)
		self.editor = editor
		self.font = font

		self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

		editor.signals.changed.connect(self.update)

	def paintEvent(self, event):
		if not self.editor.paletteOpen and not self.editor.searchMode and not self.editor.completionActive:
			return
		painter = QPainter(self)
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)

		if self.editor.searchMode:
			self.drawSearch(painter, metrics)
		if self.editor.paletteOpen:
			self.drawPalette(painter, metrics)
		if self.editor.completionActive:
			self.drawCompletion(painter, metrics)

	def drawCompletion(self, painter, metrics):
		completions = self.editor.completions
		if not completions:
			return
		rowHeight = metrics.height() + 2
		boxWidth = max(metrics.horizontalAdvance(c) for c in completions) + 24
		boxWidth = max(boxWidth, 160)
		boxHeight = len(completions) * rowHeight + 4

		paletteBg	= getColor("PALETTE_BG")
		paletteFg	= getColor("PALETTE_FG")
		selectBg	= getColor("PALETTE_SELECT_BG")
		selectFg	= getColor("PALETTE_SELECT_FG")

		cursorScreenX = getattr(self.editor, "completionX", 100)
		cursorScreenY = getattr(self.editor, "completionY", 100)

		boxX = cursorScreenX
		boxY = cursorScreenY + metrics.height() + 2
		if boxX + boxWidth > self.width():
			boxX = self.width() - boxWidth - 4
		if boxY + boxHeight > self.height():
			boxY = cursorScreenY - boxHeight - 2

		painter.fillRect(boxX, boxY, boxWidth, boxHeight, QColor(paletteBg))
		painter.setPen(QColor(paletteFg))
		painter.drawRect(boxX, boxY, boxWidth - 1, boxHeight - 1)

		cy = boxY + 2
		for i, word in enumerate(completions):
			selected = (i == self.editor.completionIndex)
			if selected:
				painter.fillRect(boxX + 1, cy, boxWidth - 2, rowHeight, QColor(selectBg))
				painter.setPen(QColor(selectFg))
			else:
				painter.setPen(QColor(paletteFg))
			painter.drawText(boxX + 8, cy + metrics.ascent(), word)
			cy += rowHeight

	def drawSearch(self, painter, metrics):
		rowHeight = metrics.height() + 8
		y = self.height() - rowHeight
		painter.fillRect(0, y, self.width(), rowHeight, QColor(getColor("PALETTE_BG")))

		painter.setPen(QColor(getColor("PALETTE_FG")))
		painter.drawLine(0, y, self.width(), y)
		painter.drawText(8, y + metrics.ascent() + 4, f"SEARCH: {self.editor.searchInput}_")
	
	def drawPalette(self, painter, metrics):
		items = self.filtered()
		rowHeight = metrics.height() + 4
		maxVisible = 12
		totalItems = len(items)
		visibleItems = min(totalItems, maxVisible)

		select = self.editor.paletteSelection
		offset = getattr(self.editor, "paletteScrollOffset", 0)
		if select < offset:
			offset = select
		elif select >= offset + maxVisible:
			offset = select - maxVisible + 1
		self.editor.paletteScrollOffset = offset

		visibleSlice = items[offset: offset + maxVisible]

		boxWidth = min(self.width() - 100, 560)
		boxHeight = rowHeight + 6 + rowHeight + 8 + len(visibleSlice) * rowHeight + rowHeight + 16
		boxX = (self.width() - boxWidth) // 2
		boxY = max(10, (self.height() - boxHeight) // 3)
		if boxY + boxHeight > self.height() - 10:
			boxY = max(10, self.height() - boxHeight - 10)
		
		paletteBg  	= getColor("PALETTE_BG")
		paletteFg  	= getColor("PALETTE_FG")
		selectBg  	= getColor("PALETTE_SELECT_BG")
		selectFg  	= getColor("PALETTE_SELECT_FG")
		titleFg		= getColor("PALETTE_TITLE")
		hintFg 		= getColor("PALETTE_HINT")

		painter.fillRect(boxX, boxY, boxWidth, boxHeight, QColor(paletteBg))
		painter.setPen(QColor(paletteFg))
		painter.drawRect(boxX, boxY, boxWidth - 1, boxHeight - 1)

		cy = boxY + 6
		titleRowY = cy + metrics.ascent()

		painter.setPen(QColor(titleFg))
		if self.editor.paletteMode == "files":
			dirPath = getattr(self.editor, "paletteDir", ".")
			maxPathWidth = boxWidth - metrics.horizontalAdvance("OPEN FILE  ") - 20
			pathString = dirPath
			while metrics.horizontalAdvance(pathString) > maxPathWidth and len(pathString) > 8:
				slash = pathString.find(os.sep, 1)
				if slash == -1:
					pathString = pathString[-20:]
					break
				pathString = "..." + pathString[4:]
			title = f"OPEN FILE {pathString}"
		else:
			title = "COMMAND PALETTE"
		painter.drawText(boxX + 8, cy + metrics.ascent(), title)
		cy += rowHeight + 4

		painter.setPen(QColor(paletteFg))
		painter.drawLine(boxX + 4, cy, boxX + boxWidth - 4, cy)
		cy += 6

		painter.drawText(boxX + 8, cy + metrics.ascent(), "> " + self.editor.paletteInput + "_")
		cy += rowHeight + 4

		painter.drawLine(boxX + 4, cy, boxX + boxWidth - 4, cy)
		cy += 6
		for i, item in enumerate(visibleSlice):
			globalIndex = offset + i
			selected = (globalIndex == select)
			if selected:
				painter.fillRect(boxX + 4, cy, boxWidth - 8, rowHeight, QColor(selectBg))
				painter.setPen(QColor(selectFg))
			else:
				painter.setPen(QColor(paletteFg))
			painter.drawText(boxX + 10, cy + metrics.ascent(), item["name"])
			cy += rowHeight
		if totalItems > maxVisible:
			painter.setPen(QColor(hintFg))
			scrollText = f"{select + 1}/{totalItems}"
			scrollWidth = metrics.horizontalAdvance(scrollText)
			painter.drawText(boxX + boxWidth - scrollWidth - 8, titleRowY, scrollText)
		cy += 4
		painter.setPen(QColor(hintFg))
		hint = "ENTER select  ESC close      ↑↓ BKSP Go Up (FILES)"
		painter.drawText(boxX + 8, cy + metrics.ascent(), hint)

	def filtered(self):
		query = self.editor.paletteInput.strip().lower()
		items = self.editor.paletteItems
		if not query:
			return items
		matched = [i for i in items if self.fuzzy(query, i["name"].lower())]
		matched.sort(key=lambda i: (
			not i["name"].lower().startswith(query),
			len(i["name"])
		))
		return matched
	
	def fuzzy(self, query, text):
		it = 0
		for ch in text:
			if it < len(query) and ch == query[it]:
				it += 1
		return it == len(query)