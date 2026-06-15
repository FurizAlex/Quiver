from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QColor
from frontend.qt.amigaPalette import getColor

class TabBar(QWidget):
	def __init__(self, editor, font: QFont):
		super().__init__()
		self.editor = editor
		self.font = font
		metrics = QFontMetrics(font)
		self.setFixedHeight(metrics.height() + 8)
		self.tabRects = []
		self.dragIndex = -1
		editor.signals.changed.connect(self.update)

	def rebuildTabRects(self):
		metrics = QFontMetrics(self.font)
		self.tabRects = []
		x = 4
		for i, buffer in enumerate(self.editor.buffers):
			name = buffer.name.upper()
			if buffer.modified:
				name += " *"
			w = metrics.horizontalAdvance(name) + 16
			self.tabRects.append((x, w, i))
			x += w + 2

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)

		tabBg		= getColor("TAB_BG")
		tabFg		= getColor("TAB_FG")
		activeBg	= getColor("TAB_ACTIVE_BG")
		activeFg	= getColor("TAB_ACTIVE_FG")

		painter.fillRect(self.rect(), QColor(tabBg))
		self.rebuildTabRects()

		for (x, w, i) in self.tabRects:
			buffer = self.editor.buffers[i]
			name = buffer.name.upper()
			if buffer.modified:
				name += " *"
			isActive = (i == self.editor.currentBuffer)
			h = self.height()

			if isActive:
				painter.fillRect(x, 0, w, h, QColor(activeBg))
				painter.setPen(QColor(getColor("PALETTE_TITLE")))
				painter.drawLine(x, h - 2, x + w, h - 2)
				painter.setPen(QColor(activeFg))
			else:
				painter.fillRect(x, 2, w, h - 2, QColor(tabBg))
				painter.setPen(QColor(tabFg))
			painter.drawText(x + 8, metrics.ascent() + 4, name)

	def tabAt(self, mouseX):
		if not self.tabRects:
			self.rebuildTabRects()
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
			self.dragIndex = index
			self.editor.currentBuffer = index
			self.editor.pane.buffer = self.editor.buffers[index]
			self.editor.pane.cursorX = 0
			self.editor.pane.cursorY = 0
			self.editor.updateScroll()
			self.editor.notifyChanged()
		elif event.button() == Qt.MouseButton.MiddleButton:
			self.closeTab(index)

	def mouseMoveEvent(self, event):
		if self.dragIndex == -1:
			return
		if not (event.buttons() & Qt.MouseButton.LeftButton):
			self.dragIndex = -1
			return
		mouseX = event.position().x()
		target = self.tabAt(mouseX)
		if target != -1 and target != self.dragIndex:
			buffers = self.editor.buffers
			buffers[self.dragIndex], buffers[target] = buffers[target], buffers[self.dragIndex]
			if self.editor.currentBuffer == self.dragIndex:
				self.editor.currentBuffer = target
			elif self.editor.currentBuffer == target:
				self.editor.currentBuffer = self.dragIndex
			self.dragIndex = target
			self.editor.notifyChanged()

	def mouseReleaseEvent(self, event):
		self.dragIndex = -1

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
			from frontend.qt.app import QuiverDialog
			outcome = QuiverDialog.ask(
				"UNSAVED CHANGES",
				f"'{buffer.name}' has unsaved changes. Close anyway?",
				self.font,
				self
			)
			if outcome != "yes":
				return
		self.editor.buffers.pop(index)
		self.editor.currentBuffer = min(self.editor.currentBuffer, len(self.editor.buffers) - 1)
		self.editor.pane.buffer = self.editor.buffers[self.editor.currentBuffer]
		self.editor.notifyChanged()