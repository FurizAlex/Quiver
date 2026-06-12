from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QColor

class TabBar(QWidget):
	def __init__(self, editor, font: QFont):
		super().__init__()
		self.editor = editor
		self.font = font
		metrics = QFontMetrics(font)
		self.setFixedHeight(metrics.height() + 8)
		self.tabRects = []
		editor.signals.changed.connect(self.update)

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)

		painter.fillRect(self.rect(), QColor("#000033"))
		self.tabRects = []

		x = 4
		for i, buffer in enumerate(self.editor.buffers):
			name = buffer.name.upper()
			if buffer.modified:
				name += " *"
			isActive = (i == self.editor.currentBuffer)
			tabWidth = metrics.horizontalAdvance(name) + 16
			tabHeight = self.height()

			if isActive:
				painter.fillRect(x, 0, tabWidth, tabHeight, QColor("#0000AA"))
				painter.setPen(QColor("#FFFFFF"))
			else:
				painter.fillRect(x, 2, tabWidth, tabHeight - 2, QColor("#000055"))
				painter.setPen(QColor("#AAAAAA"))
			painter.drawText(x + 8, metrics.ascent() + 4, name)
			self.tabRects.append((x, tabWidth, i))
			x += tabWidth + 2

	def tabAt(self, mouseX):
		for x, w, i in self.tabRects:
			if x <= mouseX < x + w:
				return i
		return -1
	
	def mousePressEvent(self, event):
		mouseX = event.position().x()
		index = self.tabAt(mouseX)
		if index == -1:
			return
		if event.button() == Qt.MouseButton.LeftButton:
			self.editor.currentBuffer = index
			self.editor.pane.buffer = self.editor.buffers[index]
			self.editor.notifyChanged()
		elif event.button() == Qt.MouseButton.MiddleButton:
			self.closeTab(index)

	def closeTab(self, index):
		if len(self.editor.buffers) <= 1:
			buffer = self.editor.buffers[0]
			buffer.lines = [""]
			buffer.filename = None
			buffer.modified = False
			self.editor.pane.cursorX = 0
			self.editor.pane.cursorY = 0
			self.editor.notifyChanged()
			return
		buffer = self.editor.buffers[index]
		if buffer.modified:
			from PyQt6.QtWidgets import QMessageBox
			reply = QMessageBox.question(
				self,
				"UNSAVED CHANGES",
				f"'{buffer.name}' has unsaved changes. Close anyway?",
				QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
				QMessageBox.StandardButton.No
			)
			if reply != QMessageBox.StandardButton.Yes:
				return
		self.editor.buffers.pop(index)
		self.editor.currentBuffer = min(self.editor.currentBuffer, len(self.editor.buffers) - 1)
		self.editor.pane.buffer = self.editor.buffers[self.editor.currentBuffer]
		self.editor.notifyChanged()