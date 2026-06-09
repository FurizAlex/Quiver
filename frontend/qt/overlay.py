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
		contentRows = min(len(items), 10)
		height = 32 + rowHeight + contentRows * rowHeight + rowHeight + 16
		width = min(self.width() - 80, 600)
		x = (self.width() - width) // 2
		y = (self.height() - height) // 3

		painter.fillRect(x, y, width, height, QColor("#0000AA"))
		painter.setPen(QColor("#FFFFFF"))
		painter.drawRect(x, y, width - 1, height - 1)

		painter.setPen(QColor("#FFFF55"))
		painter.drawText(x + 8, y + metrics.ascent() + 6, "COMMAND PALETTE")

		painter.setPen(QColor("#FFFFFF"))
		inputY = y + 8 + rowHeight
		painter.drawText(x + 8, inputY + metrics.ascent(), "> " + self.editor.paletteInput + "_")

		painter.setPen(QColor("#FFFFFF"))
		divY = inputY + rowHeight + 2
		painter.drawLine(x + 4, divY, x + width - 4, divY)

		itemY = divY + 8
		for i, item in enumerate(items[:10]):
			selected = (i == self.editor.paletteSelection)
			if selected:
				painter.fillRect(x + 4, itemY - metrics.ascent() + 2, width - 8, rowHeight, QColor("#FFFFFF"))
				painter.setPen(QColor("#0000AA"))
			else:
				painter.setPen(QColor("#FFFFFF"))
			painter.drawText(x + 10, itemY + metrics.ascent() - metrics.ascent() + rowHeight // 2 + metrics.ascent() // 2, item["name"])
			itemY += rowHeight
		painter.setPen(QColor("#AAAAAA"))
		hintY = y + height - 6
		painter.drawText(x + 8, hintY, "ENTER execute   ESC close   UP/DOWN navigate")
	
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