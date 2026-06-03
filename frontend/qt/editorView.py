from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics

from frontend.qt.amigaPalette import *
from frontend.qt.qtTranslator import translateKey, translateMouse

class EditorView(QWidget):
	cursorChanged = pyqtSignal(int, int)
	def __init__(self, editor):
		super().__init__()
		self.editor = editor
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

		font = QFont("Courier New")
		font.setPointSize(14)
		self.setFont(font)
		self.gutterWidth = 60

		self.editor.signals.changed.connect(self.update)

	def resizeEvent(self, event):
		self.editor.resize(self.width(), self.height())
		super().resizeEvent(event)

	def paintEvent(self, event):
		painter = QPainter(self)
		self.drawBackground(painter)
		self.drawGutter(painter)
		self.drawText(painter)
		self.drawCursor(painter)
		self.drawSelection(painter)

	def drawBackground(self, painter):
		painter.fillRect(self.rect(), QColor(BACKGROUND))

	def drawGutter(self, painter):
		painter.fillRect(0, 0, self.gutterWidth, self.height(), QColor(GUTTER))

	def drawText(self, painter):
		metrics = QFontMetrics(self.font())
		lineHeight = metrics.height()
		pane = self.editor.pane
		visibleCount = self.height() // lineHeight + 1
		visibleLines = pane.buffer.lines[pane.scrollY: pane.scrollY + visibleCount]
		y = lineHeight

		for lineNumber, text in enumerate(visibleLines):
			painter.setPen(QColor(TEXT))
			painter.drawText(self.gutterWidth + 8, y, text)
			self.drawLineNumber(painter, pane.scrollY + lineNumber, y)
			y += lineHeight

	def drawLineNumber(self, painter, lineNumber, y):
		painter.setPen(QColor(COMMENT))
		text = str(lineNumber + 1)

		painter.drawText(8, y, text.rjust(4))

	def drawCursor(self, painter):
		pane = self.editor.pane
		metrics = QFontMetrics(self.font())
		charWidth = metrics.horizontalAdvance("M")
		lineHeight = metrics.height()
		x = self.gutterWidth + 8 + ((pane.cursorX - pane.scrollX) * charWidth)
		y = ((pane.cursorY - pane.scrollY + 1) * lineHeight)
		painter.fillRect(x, y - lineHeight + 2, 2, lineHeight, QColor(TEXT))

	def drawSelection(self, painter):
		pass

	def keyPressEvent(self, event):
		inputEvent = translateKey(event)
		self.editor.handleInput(inputEvent)
		self.editor.updateScroll()
		self.update()
		self.emitCursor()

	def mousePressEvent(self, event):
		inputEvent = translateMouse(event)
		self.editor.handleInput(inputEvent)
		self.editor.updateScroll()
		self.update()
		self.emitCursor()

	def emitCursor(self):
		pane = self.editor.pane

		line = pane.cursorY + 1
		col = pane.cursorX + 1
		self.cursorChanged.emit(line, col)
