from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter, QPlainTextEdit, QVBoxLayout
from PyQt6.QtGui import QPainter, QColor, QFontDatabase, QFont, QFontMetrics, QTextFormat
from PyQt6.QtWidgets import QTextEdit

from frontend.qt.paneContainer import PaneContainer
from frontend.qt.overlay import OverlayWidget
from frontend.qt.amigaPalette import *
from frontend.qt.qtTranslator import translateKey, translateMouse
from syntax.lexer import Lexer

class EditorView(QWidget):
	cursorChanged = pyqtSignal(int, int)
	def __init__(self, editor):
		super().__init__()
		self.editor = editor
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
		fontID = QFontDatabase.addApplicationFont("assets/fonts/Perfect DOS VGA 437.ttf")
		if fontID != -1:
			family = QFontDatabase.applicationFontFamilies(fontID)[0]
		else:
			family = "Courier New"
		font = QFont(family)
		font.setPixelSize(16)
		font.setBold(True)
		font.setStyleHint(QFont.StyleHint.TypeWriter)
		self.setFont(font)

		self.paneContainer = PaneContainer(editor, font)

		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)
		layout.addWidget(self.paneContainer)

		self.overlay = OverlayWidget(editor, font, parent=self)
		self.overlay.resize(self.size())
		self.overlay.raise_()

		self.editor.signals.changed.connect(self.update)

	def paintEvent(self, event):
		pass

	def resizeEvent(self, event):
		self.editor.resize(self.width(), self.height())
		super().resizeEvent(event)

class PaneView(QWidget):
	cursorChanged = pyqtSignal(int, int)
	def __init__(self, editor, pane, font, paneIndex=0):
		super().__init__()

		self.editor = editor
		self.pane = pane
		self.font = font

		self.paneIndex = paneIndex
		self.gutterWidth = 52
		self.lexer = Lexer()

		self.setFont(font)
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
		editor.signals.changed.connect(self.update)

	def paintEvent(self, event):
		painter = QPainter(self)
		self.drawBackground(painter)
		self.drawGutter(painter)
		self.drawCurrentLine(painter)
		self.drawSelection(painter)
		self.drawText(painter)
		self.drawCursor(painter)

	def drawBackground(self, painter):
		painter.fillRect(self.rect(), QColor(BACKGROUND))

	def drawGutter(self, painter):
		painter.fillRect(0, 0, self.gutterWidth, self.height(), QColor(GUTTER))
		painter.setPen(QColor(GUTTER_SEP))
		painter.drawLine(self.gutterWidth, 0, self.gutterWidth, self.height())
		metrics = QFontMetrics(self.font)
		pane = self.pane
		visibleCount = self.height() // metrics.height() + 1
		for i in range(visibleCount):
			bufferY = pane.scrollY + i
			if bufferY >= len(pane.buffer.lines):
				break
			self.drawLineNumber(painter, bufferY, i * metrics.height())

	def drawText(self, painter):
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		pane = self.pane
		visibleCount = self.height() // lineHeight + 1
		visibleLines = pane.buffer.lines[pane.scrollY: pane.scrollY + visibleCount]

		for lineIndex, line in enumerate(visibleLines):
			bufferY = pane.scrollY + lineIndex
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
						col = (x - self.gutterWidth - 8) // metrics.horizontalAdvance(" ")
						spaces = tabStop - (col % tabStop)
						x += metrics.horizontalAdvance(" ") * spaces
						bufferX += 1
					else:
						painter.setPen(self.tokenColor(tokenType))
						painter.drawText(x, lineIndex * lineHeight + metrics.ascent(), ch)
						x += metrics.horizontalAdvance(ch)
						bufferX += 1

	def drawLineNumber(self, painter, lineNumber, y):
		metrics = QFontMetrics(self.font)
		if lineNumber == self.pane.cursorY:
			painter.setPen(QColor("#FFFFFF"))
		else:
			painter.setPen(QColor(COMMENT))
		text = str(lineNumber + 1).rjust(4)
		painter.drawText(4, y + metrics.ascent(), text)

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
		painter.fillRect(x, y, charWidth, lineHeight, QColor(CURSOR))
		try:
			ch = pane.buffer.lines[pane.cursorY][pane.cursorX]
		except IndexError:
			ch = " "
		painter.setPen(QColor(BACKGROUND))
		painter.drawText(x, y + metrics.ascent(), ch)

	def drawCurrentLine(self, painter):
		pane = self.pane
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		visibleY = pane.cursorY - pane.scrollY
		if visibleY < 0:
			return
		y = visibleY * lineHeight
		painter.fillRect(self.gutterWidth + 1, y, self.width() - self.gutterWidth - 1, lineHeight, QColor(CURRENT_LINE))

	def drawSelection(self, painter):
		pane = self.pane
		selection = self.editor.selection
		if not selection.active:
			return
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
			x = self.gutterWidth + 1 + (startCol - pane.scrollX) * charWidth
			w = (endCol - startCol) * charWidth
			y = visibleLine * lineHeight
			painter.fillRect(x, y, w, lineHeight, QColor(SELECTION))

	def tokenColor(self, tokenType):
		colors = {
			"keyword": KEYWORD,
			"string": STRING,
			"comment": COMMENT,
			"text": TEXT,
		}
		return QColor(colors.get(tokenType, TEXT))

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

		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		charWidth = metrics.horizontalAdvance("M")

		px = event.position().x()
		py = event.position().y()

		col = max(0, int((px - self.gutterWidth - 8) / charWidth)) + self.pane.scrollX
		row = int(py / lineHeight) + self.pane.scrollY

		row = max(0, min(row, len(self.pane.buffer.lines) - 1))
		col = max(0, min(col, len(self.pane.buffer.lines[row])))

		self.pane.cursorX = col
		self.pane.cursorY = row

		self.editor.updateScroll()
		self.editor.notifyChanged()
		self.cursorChanged.emit(self.pane.cursorY + 1, self.pane.cursorX + 1)

	def visualColumn(self, text):
		expanded = text.replace("\t", " " * self.editor.settings.tabSize)
		return QFontMetrics(self.font).horizontalAdvance(expanded)