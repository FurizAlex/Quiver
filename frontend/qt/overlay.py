from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFontMetrics
from PyQt6.QtCore import Qt

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
		if not self.editor.paletteOpen and not self.editor.searchMode:
			return
		painter = QPainter(self)
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)

		if self.editor.searchMode:
			self.drawSearch(painter, metrics)
		if self.editor.paletteOpen:
			self.drawPalette(painter, metrics)

	def drawSearch(self, painter, metrics):
		rowHeight = metrics.height() + 8
		y = self.height() - rowHeight
		painter.fillRect(0, y, self.width(), rowHeight, QColor("#0000AA"))

		painter.setPen(QColor("#FFFFFF"))
		painter.drawLine(0, y, self.width(), y)
		painter.drawText(8, y + metrics.ascent() + 4, f"SEARCH: {self.editor.searchInput}_")
	
	def drawPalette(self, painter, metrics):
		items = self.filtered()
		rowHeight = metrics.height() + 4
		visibleItems = min(len(items), 14)

		boxWidth = min(self.width() - 100, 620)
		boxHeight = rowHeight + 6 + rowHeight + 6 + visibleItems * rowHeight + rowHeight + 16
		boxX = (self.width() - boxWidth) // 2
		boxY = max(10, (self.height() - boxHeight) // 3)

		if boxY + boxHeight > self.height() - 10:
			boxY = max(10, self.height() - boxHeight - 10)

		painter.fillRect(boxX, boxY, boxWidth, boxHeight, QColor("#0000AA"))
		painter.setPen(QColor("#FFFFFF"))
		painter.drawRect(boxX, boxY, boxWidth - 1, boxHeight - 1)

		cy = boxY + 6

		painter.setPen(QColor("#FFFF55"))
		painter.drawText(boxX + 8, cy + metrics.ascent(), "COMMAND PALETTE")
		cy += rowHeight + 4

		painter.setPen(QColor("#FFFFFF"))
		painter.drawLine(boxX + 4, cy, boxX + boxWidth - 4, cy)
		cy += 6

		painter.drawText(boxX + 8, cy + metrics.ascent(), "> " + self.editor.paletteInput + "_")
		cy += rowHeight + 4

		painter.drawLine(boxX + 4, cy, boxX + boxWidth - 4, cy)
		cy += 6
		for i, item in enumerate(items[:10]):
			selected = (i == self.editor.paletteSelection)
			if selected:
				painter.fillRect(boxX + 4, cy, boxWidth - 8, rowHeight, QColor("#FFFFFF"))
				painter.setPen(QColor("#0000AA"))
			else:
				painter.setPen(QColor("#FFFFFF"))
			painter.drawText(boxX + 10, cy + metrics.ascent(), item["name"])
			cy += rowHeight
		cy += 4
		painter.setPen(QColor("#AAAAAA"))
		painter.drawText(boxX + 8, cy + metrics.ascent(), "ENTER execute   ESC close   UP/DOWN navigate")

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