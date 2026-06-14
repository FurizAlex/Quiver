from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter, QPlainTextEdit, QVBoxLayout
from PyQt6.QtGui import QPainter, QColor, QFontDatabase, QFont, QFontMetrics, QTextFormat
from PyQt6.QtWidgets import QTextEdit

from frontend.qt.paneContainer import PaneContainer
from frontend.qt.overlay import OverlayWidget
from frontend.qt.amigaPalette import getColor
from frontend.qt.qtTranslator import translateKey
from syntax.lexer import Lexer

class EditorView(QWidget):
	cursorChanged = pyqtSignal(int, int)
	def __init__(self, editor, font: QFont):
		super().__init__()
		self.editor = editor
		self.editorFont = font
		self.setFont(font)
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
		self.paneContainer = PaneContainer(editor, self.editorFont)

		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)
		layout.addWidget(self.paneContainer)

		self.overlay = OverlayWidget(editor, self.editorFont, parent=self)
		self.overlay.resize(self.size())
		self.overlay.raise_()

		self.editor.signals.changed.connect(self.update)

	def paintEvent(self, event):
		pass

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self.overlay.resize(self.size())
		self.overlay.raise_()
		self.editor.resize(self.width(), self.height())

class PaneView(QWidget):
	cursorChanged = pyqtSignal(int, int)
	def __init__(self, editor, pane, font: QFont, paneIndex=0):
		super().__init__()

		self.editor = editor
		self.pane = pane
		self.font = font

		self.paneIndex = paneIndex
		self.lexer = Lexer()

		self.setFont(font)

		metrics = QFontMetrics(font)
		self.gutterWidth = metrics.horizontalAdvance("0000") + 40
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
		editor.signals.changed.connect(self.update)

	def paintEvent(self, event):
		try:
			painter = QPainter(self)
			painter.setFont(self.font)
			self.drawBackground(painter)
			self.drawCurrentLine(painter)
			self.drawSelection(painter)
			self.drawText(painter)
			self.drawGutter(painter)
			self.drawCursor(painter)
		except Exception:
			import traceback
			traceback.print_exc()

	def drawBackground(self, painter):
		painter.fillRect(self.rect(), QColor(getColor("BACKGROUND")))

	def drawGutter(self, painter):
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		pane = self.pane

		painter.fillRect(0, 0, self.gutterWidth, self.height(), QColor(getColor("GUTTER")))

		visibleCount = self.height() // lineHeight + 1
		for i in range(visibleCount):
			bufferY = pane.scrollY + i
			if bufferY >= len(pane.buffer.lines):
				break
			isCurrent = (bufferY == pane.cursorY)
			painter.setPen(QColor("#FFFFFF") if isCurrent else QColor(getColor("COMMENT")))
			text = str(bufferY + 1)
			textWidth = metrics.horizontalAdvance(text)
			x = self.gutterWidth - textWidth - 10
			y = i * lineHeight + metrics.ascent()
			painter.drawText(x, y, text)

	def drawText(self, painter):
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		charWidth = metrics.horizontalAdvance("M")
		pane = self.pane
		visibleCount = self.height() // lineHeight + 1
		lines = pane.buffer.lines[pane.scrollY: pane.scrollY + visibleCount]

		for lineIndex, line in enumerate(lines):
			tokens = self.lexer.tokenize(line, pane.buffer.language)
			x = self.gutterWidth + 8
			bufferX = 0
			for tokenText, tokenType in tokens:
				for ch in tokenText:
					if bufferX < pane.scrollX:
						bufferX += 1
						continue
					if ch == "\t":
						tabStop = self.editor.settings.tabSize
						col = (x - self.gutterWidth - 8) // charWidth
						spaces = tabStop - (col % tabStop)
						x += charWidth * spaces
						bufferX += 1
					else:
						painter.setPen(self.tokenColor(tokenType))
						painter.drawText(x, lineIndex * lineHeight + metrics.ascent(), ch)
						x += charWidth
						bufferX += 1

	def drawLineNumber(self, painter, lineNumber, y):
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)
		isCurrentLine = (lineNumber == self.pane.cursorY)
		painter.setPen(QColor("#FFFFFF") if isCurrentLine else QColor(getColor("CURRENT_LINE")))
		text = str(lineNumber + 1).rjust(4)
		painter.drawText(self.gutterWidth - metrics.horizontalAdvance("9999") - 4, y + metrics.ascent(), text)

	def drawCursor(self, painter):
		pane = self.pane
		if self.paneIndex != self.editor.activePane:
			return
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		charWidth = metrics.horizontalAdvance("M")
		visibleY = pane.cursorY - pane.scrollY
		if visibleY < 0:
			return
		y = visibleY * lineHeight
		x = self.gutterWidth + 8 + (pane.cursorX - pane.scrollX) * charWidth
		painter.fillRect(x, y, charWidth, lineHeight, QColor(getColor("CURSOR")))
		try:
			ch = pane.buffer.lines[pane.cursorY][pane.cursorX]
		except IndexError:
			ch = " "
		painter.setPen(QColor(getColor("BACKGROUND")))
		painter.drawText(x, y + metrics.ascent(), ch)

	def drawCurrentLine(self, painter):
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		visibleY = self.pane.cursorY - self.pane.scrollY
		if visibleY < 0:
			return
		y = visibleY * lineHeight
		painter.fillRect(self.gutterWidth + 1, y, self.width() - self.gutterWidth - 1, lineHeight, QColor(getColor("CURRENT_LINE")))

	def drawSelection(self, painter):
		pane = self.pane
		selection = self.editor.selection
		if not selection.active:
			return
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		charWidth = metrics.horizontalAdvance("M")
		visibleCount = self.height() // lineHeight + 1
		for visibleLine in range(visibleCount):
			bufferY = pane.scrollY + visibleLine
			selectionRange = selection.selectedColumns(bufferY)
			if selectionRange is None:
				continue
			startCol, endCol = selectionRange
			if startCol is None:
				startCol = 0
			if endCol is None:
				try:
					endCol = len(pane.buffer.lines[bufferY])
				except IndexError:
					endCol = startCol
			x = self.gutterWidth + 8 + (startCol - pane.scrollX) * charWidth
			w = (endCol - startCol) * charWidth
			y = visibleLine * lineHeight
			painter.fillRect(x, y, w, lineHeight, QColor(getColor("SELECTION")))
			try:
				line = pane.buffer.lines[bufferY]
			except IndexError:
				continue
			painter.setPen(QColor(getColor("SELECTION_TEXT")))
			for col in range(startCol, endCol):
				if col < pane.scrollX:
					continue
				if col >= len(line):
					break
				ch = line[col]
				cx = self.gutterWidth + 8 + (col - pane.scrollX) * charWidth
				painter.drawText(cx, y + metrics.ascent(), ch)

	def tokenColor(self, tokenType):
		mapping = {
			"keyword": "KEYWORD",
			"string": "STRING",
			"comment": "COMMENT",
			"text": "TEXT",
			"number": "NUMBER",
		}
		return QColor(getColor(mapping.get(tokenType, "TEXT")))

	def keyPressEvent(self, event):
		self.editor.activePane = self.paneIndex
		inputEvent = translateKey(event)
		self.editor.handleInput(inputEvent)
		self.editor.updateScroll()
		self.editor.notifyChanged()
		self.cursorChanged.emit(self.pane.cursorY + 1, self.pane.cursorX + 1)

	def mousePressEvent(self, event):
		self.editor.activePane = self.paneIndex
		self.setFocus()
		row, col = self.pixelToRowCol(event.position().x(), event.position().y())
		self.pane.cursorX = col
		self.pane.cursorY = row
		self.dragStartRow = row
		self.dragStartCol = col
		self.dragging = True
		self.editor.selection.clear()
		self.editor.updateScroll()
		self.editor.notifyChanged()
		self.cursorChanged.emit(row + 1, col + 1)

	def mouseMoveEvent(self, event):
		if getattr(self, "dragging", False):
			row, col = self.pixelToRowCol(event.position().x(), event.position().y())
			if not self.editor.selection.active:
				if row != self.dragStartRow or col != self.dragStartCol:
					self.editor.selection.begin(self.dragStartCol, self.dragStartRow)
			if self.editor.selection.active:
				self.editor.selection.update(col, row)
				self.pane.cursorX = col
				self.pane.cursorY = row
				self.editor.notifyChanged()

	def mouseReleaseEvent(self, event):
		self.dragging = False
		self.editor.notifyChanged()

	def wheelEvent(self, event):
		delta = event.angleDelta().y()
		lines = 3
		if delta > 0:
			self.pane.scrollY = max(0, self.pane.scrollY - lines)
		else:
			maxScroll = max(0, len(self.pane.buffer.lines) - 1)
			self.pane.scrollY = min(maxScroll, self.pane.scrollY + lines)
		self.editor.notifyChanged()

	def pixelToRowCol(self, px, py):
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		charWidth = metrics.horizontalAdvance("M")
		col = max(0, int((px - self.gutterWidth - 8) / charWidth)) + self.pane.scrollX
		row = int(py / lineHeight) + self.pane.scrollY
		row = max(0, min(row, len(self.pane.buffer.lines) - 1))
		col = max(0, min(col, len(self.pane.buffer.lines[row])))
		return row, col