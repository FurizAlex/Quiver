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

	def focusNextPane(self):
		if not self.panes:
			return
		current = self.activePane
		index = self.panes.index(current)
		nextIndex = (index + 1) % len(self.panes)

		self.setActivePane(self.panes[nextIndex])

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