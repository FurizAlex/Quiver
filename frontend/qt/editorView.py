from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter, QPlainTextEdit
from PyQt6.QtGui import QPainter, QColor, QFontDatabase, QFont, QFontMetrics, QTextFormat
from PyQt6.QtWidgets import QTextEdit

from frontend.qt.amigaPalette import *
from frontend.qt.qtTranslator import translateKey, translateMouse
from syntax.lexer import Lexer

class EditorView(QWidget):
	cursorChanged = pyqtSignal(int, int)
	def __init__(self, editor):
		super().__init__()
		self.editor = editor
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
		font_id = QFontDatabase.addApplicationFont("assets/fonts/Perfect DOS VGA 437.ttf")
		family = QFontDatabase.applicationFontFamilies(font_id)[0]
		font = QFont(family)
		font.setPixelSize(16)
		font.setBold(True)
		font.setStyleHint(QFont.StyleHint.TypeWriter)

		self.textEditors = []

		self.setFont(font)
		self.gutterWidth = 60
		self.lexer = Lexer()
		self.editor.signals.changed.connect(self.update)

	def resizeEvent(self, event):
		self.editor.resize(self.width(), self.height())
		super().resizeEvent(event)

	def drawSearchBar(self, painter):
		metrics = QFontMetrics(self.font())
		height =  metrics.height() + 8
		y = self.height() - height

		painter.fillRect(0, y, self.width(), height, QColor("#0000AA"))
		painter.setPen(QColor("#FFFFFF"))
		painter.drawText(8, y + metrics.height(), f"SEARCH: {self.editor.searchInput}")
		
	def drawPalette(self, painter):
		metrics = QFontMetrics(self.font())
		items = self.filteredPaletteItems()
		width = 500
		height = min(len(items), 10) * metrics.height()
		height += 80
		x = (self.width() - width) // 2
		y = (self.width() - height) // 2

		painter.fillRect(x, y, width, height, QColor("#0000AA"))
		painter.setPen(QColor("#FFFFFF"))
		painter.drawRect(x, y, width, height)
		painter.drawText(x + 8, y + 20, "COMMAND PALETTE")
		painter.drawText(x + 8, y + 45, "> " + self.editor.paletteInput)

		rowY = y + 70
		for index, item in enumerate(items[:10]):
			selected = index == self.editor.paletteSelection
			if selected:
				painter.fillRect(x + 4, rowY - metrics.height() + 4, width - 8, metrics.height(), QColor("#FFFFFF"))
				painter.setPen(QColor("#0000AA"))
			else:
				painter.setPen(QColor("#FFFFFF"))
			painter.drawText(x + 8, rowY, item["name"])
			rowY += metrics.height()

	def filteredPaletteItems(self):
		query = self.editor.paletteInput.strip()
		if not query:
			return self.editor.paletteItems
		items = []

		for item in self.editor.paletteItems:
			if self.fuzzyMatch(query, item["name"]):
				items.append(item)
		items.sort(
			key=lambda item: (
				not item["name"].lower().startswith(
					query.lower()
				),
				len(item["name"])
			)
		)
		return items
	
	def fuzzyMatch(self, query, text):
		query = query.lower()
		text = text.lower()
		i = 0

		for ch in text:
			if i < len(query) and ch == query[i]:
				i += 1
		return i == len(query)
	
	def rebuildPanes(self):
		while self.splitter.count():
			widget = self.splitter.widget(0)

			self.splitter.removeWidget(widget)
			widget.deleteLater()
		self.paneViews.clear()
		for pane in self.editor.panes:
			view = PaneView(self.editor, pane)
			self.splitter.addWidget(view)
			self.paneViews.append(view)

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
	
class PaneView(QWidget):
	def paintEvent(self, event):
		painter = QPainter(self)
		self.drawBackground(painter)
		self.drawGutter(painter)
		self.drawCurrentLine(painter)
		self.drawSelection(painter)
		self.drawText(painter)
		self.drawCursor(painter)
		if self.editor.searchMode:
			self.drawSearchBar(painter)
		if self.editor.paletteOpen:
			self.drawPalette(painter)

	def drawBackground(self, painter):
		painter.fillRect(self.rect(), QColor(BACKGROUND))

	def drawGutter(self, painter):
		painter.fillRect(0, 0, self.gutterWidth, self.height(), QColor(GUTTER))

	def drawText(self, painter):
		metrics = QFontMetrics(self.font())
		lineHeight = metrics.height()
		charWidth = metrics.horizontalAdvance("M")
		pane = self.editor.pane
		visibleCount = self.height() // lineHeight + 1
		visibleLines = pane.buffer.lines[pane.scrollY: pane.scrollY + visibleCount]
		y = 0

		for lineNumber, line in enumerate(visibleLines):
			bufferY = pane.scrollY + lineNumber
			self.drawLineNumber(painter, bufferY, y)
			language = pane.buffer.language
			tokens = self.lexer.tokenize(line, language)
			x = self.gutterWidth + 8
			for tokenText, tokenType in tokens:
				painter.setPen(self.tokenColor(tokenType))
				painter.drawText(x, y + lineHeight - metrics.descent(), tokenText)
				x += len(tokenText) * charWidth
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
		visibleY = pane.cursorY - pane.scrollY
		y = visibleY * lineHeight
		painter.fillRect(x, y, 2, lineHeight, QColor(TEXT))

	def drawCurrentLine(self, painter):
		pane = self.editor.pane
		metrics = QFontMetrics(self.font())
		lineHeight = metrics.height()
		visibleY = pane.cursorY - pane.scrollY
		if visibleY < 0:
			return
		y = visibleY * lineHeight
		painter.fillRect(self.gutterWidth, y, self.width(), lineHeight, QColor("#0040A0"))

	def drawSelection(self, painter):
		pane = self.editor.pane
		selection = self.editor.selection
		if not selection.active:
			return
		metrics = QFontMetrics(self.font())
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
			startX = self.gutterWidth + 8 + (startCol - pane.scrollX) * charWidth
			if endCol is None:
				try:
					lineLength = len(pane.buffer.lines[bufferY])
				except IndexError:
					lineLength = startCol
				endCol = lineLength
			width = (endCol - startCol) * charWidth
			y = visibleLine * lineHeight
			painter.fillRect(startX, y, width, lineHeight, QColor("#3366CC"))

	def tokenColor(self, tokenType):
		colors = {
			"keyboard": KEYWORD,
			"string": STRING,
			"comment": COMMENT,
			"text": TEXT,
		}
		return QColor(colors.get(tokenType, TEXT))