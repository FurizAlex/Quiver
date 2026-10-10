from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPointF
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter, QPlainTextEdit, QVBoxLayout
from PyQt6.QtGui import QPainter, QColor, QFontDatabase, QFont, QFontMetrics, QTextFormat, QImage
from PyQt6.QtWidgets import QTextEdit

from frontend.qt.amigaPalette import getColorForLanguage

from frontend.qt.paneContainer import PaneContainer
from frontend.qt.overlay import OverlayWidget
from frontend.qt.amigaPalette import getColor, buildDitherImage, loadBackgroundImage
from frontend.qt.qtTranslator import translateKey
from syntax.lexer import Lexer
from commands.tabCommands import rememberView, restoreView

import math

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
	TEXT_PADDING = 8
	SHOW_INDENT_GUIDES = True
	cursorChanged = pyqtSignal(int, int)
	def __init__(self, editor, pane, font: QFont, paneIndex=0):
		super().__init__()
		self.cursorTrail = []
		self.TRAIL_LENGTH = 4
		self.mouseSelecting = False
		self._viewBuffer = None
		self._lastView = None
		self._lastCursor = None
		self._lastScroll = None
		self._wheelX = 0
		self._wheelY = 0

		self.editor = editor
		self.pane = pane
		self.font = font

		self.cursorScaleY = 1.0
		self.cursorTargetScaleY = 1.0
		self.lastCursorRow = 0

		self.backgroundImage = None
		self.backgroundImageSize = None
		self.backgroundImagePath = None
		self.gutterImage = None
		self.gutterImageSize = None

		self.transitionTimer = QTimer(self)
		self.transitionTimer.setInterval(16)
		self.transitionTimer.timeout.connect(self.tickTransition)
		self.transitionProgress = 1.0
		self.transitionDuration = 300
		self.transitionElapsed = 0
		self.previousBackgroundImage = None

		self.resizeDebounce = QTimer(self)
		self.resizeDebounce.setSingleShot(True)
		self.resizeDebounce.setInterval(120)
		self.resizeDebounce.timeout.connect(self.rebuildBackgroundImage)

		self.diffCache = {}
		self.diffCacheFile = None

		self.cursorAnimX = None
		self.cursorAnimY = None
		self.cursorTargetX = 0
		self.cursorTargetY = 0
		self.animTimer = QTimer(self)
		self.animTimer.setInterval(16)
		self.animTimer.timeout.connect(self.tickCursorAnim)
		self.animTimer.start()

		self.paneIndex = paneIndex
		self.lexer = Lexer()

		self.setFont(font)

		metrics = QFontMetrics(font)
		self.gutterWidth = metrics.horizontalAdvance("0000") + 40
		self.textX = self.gutterWidth + self.TEXT_PADDING
		pane.lineHeight = metrics.height()
		pane.charWidth = metrics.horizontalAdvance("M")
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
		editor.signals.changed.connect(self.update)

	def updateVisibleDimensions(self):
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		charWidth = metrics.horizontalAdvance("M")
		digits = max(4, len(str(len(self.pane.buffer.lines))))
		gutterWidth = metrics.horizontalAdvance("0" * digits) + 40
		if gutterWidth != self.gutterWidth:
			self.gutterWidth = gutterWidth
			self.textX = gutterWidth + self.TEXT_PADDING
		textAreaW = self.width() - self.textX
		self.pane.lineHeight = lineHeight
		self.pane.charWidth = charWidth
		self.pane.visibleLines = max(1, self.height() // lineHeight)
		self.pane.visibleCols = max(1, textAreaW // charWidth)

	def visualColumnOf(self, line, x):
		tabSize = max(1, self.editor.settings.tabSize)
		col = 0
		for ch in line[:x]:
			if ch == "\t":
				col += tabSize - (col % tabSize)
			else:
				col += 1
		return col

	def ensureCursorVisibleX(self):
		pane = self.pane
		try:
			line = pane.buffer.lines[pane.cursorY]
		except IndexError:
			return
		column = self.visualColumnOf(line, pane.cursorX)
		cols = max(1, pane.visibleCols)
		margin = min(4, cols // 4)
		if column < pane.scrollX + margin:
			pane.scrollX = max(0, column - margin)
		elif column >= pane.scrollX + cols - margin:
			pane.scrollX = column - cols + margin + 1

	def followCursor(self):
		"""Scroll horizontally only when the cursor actually moved (so shift+wheel scrolling sticks)."""
		pane = self.pane
		here = (id(pane.buffer), pane.cursorX, pane.cursorY)
		if here != self._lastCursor:
			self._lastCursor = here
			self.ensureCursorVisibleX()

	def maxScrollX(self):
		pane = self.pane
		tabSize = max(1, self.editor.settings.tabSize)
		first = pane.scrollY
		widest = 0
		for line in pane.buffer.lines[first: first + pane.visibleLines + 1]:
			widest = max(widest, len(line.expandtabs(tabSize)))
		return max(0, widest - 1)

	def carryCursorWithScroll(self):
		"""Scrolling moves the text, so move the animated cursor by the same amount.
		Must run at paint time too: the repaint caused by a scroll happens before the animation timer."""
		scroll = (self.pane.scrollX, self.pane.scrollY)
		last = self._lastScroll
		self._lastScroll = scroll
		if last is None or scroll == last or self.cursorAnimX is None:
			return False
		metrics = QFontMetrics(self.font)
		self.cursorAnimX -= (scroll[0] - last[0]) * metrics.horizontalAdvance("M")
		self.cursorAnimY -= (scroll[1] - last[1]) * metrics.height()
		self.cursorTrail.clear()
		return True

	def snapCursor(self):
		self.cursorAnimX = None
		self.cursorAnimY = None
		self.cursorTrail.clear()

	def syncBufferView(self):
		"""When the buffer shown by this pane changes (tab click, explorer, ctrl+tab...)
		restore that buffer's own cursor/scroll instead of reusing the previous file's."""
		pane = self.pane
		buffer = pane.buffer
		current = (pane.cursorX, pane.cursorY, getattr(pane, "scrollX", 0), getattr(pane, "scrollY", 0))
		if self._viewBuffer is not buffer:
			if self._viewBuffer is not None:
				if current == self._lastView:
					restoreView(self.editor, pane, buffer)
				else:
					lastLine = max(0, len(buffer.lines) - 1)
					pane.cursorY = max(0, min(pane.cursorY, lastLine))
					pane.cursorX = max(0, min(pane.cursorX, len(buffer.lines[pane.cursorY])))
				self.snapCursor()
			self._viewBuffer = buffer
		rememberView(self.editor, pane, buffer)
		self._lastView = (pane.cursorX, pane.cursorY, getattr(pane, "scrollX", 0), getattr(pane, "scrollY", 0))

	def paintEvent(self, event):
		try:
			self.updateVisibleDimensions()
			self.syncBufferView()
			self.followCursor()
			self.carryCursorWithScroll()
			painter = QPainter(self)
			painter.setFont(self.font)
			self.drawBackground(painter)
			self.drawCurrentLine(painter)
			self.drawSelection(painter)
			self.drawIndentGuides(painter)
			self.drawText(painter)
			self.drawGutter(painter)
			self.drawCursor(painter)
			if self.paneIndex == self.editor.activePane:
				self.storeCursorScreenPos()
		except Exception:
			import traceback
			traceback.print_exc()

	def cursorPixelPos(self):
		pane = self.pane
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		try:
			line = pane.buffer.lines[pane.cursorY]
		except IndexError:
			line = ""
		x = self.cursorXToPixel(line, pane.cursorX)
		y = (pane.cursorY - pane.scrollY) * lineHeight
		return x, y
	
	def tickCursorAnim(self):
		if not self.isVisible():
			return
		scrolled = self.carryCursorWithScroll()
		tx, ty = self.cursorPixelPos()
		if self.cursorAnimX is None:
			self.cursorAnimX = float(tx)
			self.cursorAnimY = float(ty)
			self.lastCursorRow = self.pane.cursorY
			self.cursorScaleY = 1.0
			self.update()
			return

		if self.pane.cursorY != self.lastCursorRow:
			self.cursorScaleY = 0.08
			self.lastCursorRow = self.pane.cursorY
			self.cursorTrail.clear()

		self.cursorScaleY += (1.0 - self.cursorScaleY) * 0.12
		if abs(1.0 - self.cursorScaleY) < 0.01:
			self.cursorScaleY = 1.0
		speed = 0.3
		dx = tx - self.cursorAnimX
		dy = ty - self.cursorAnimY
		moved = abs(dx) > 0.5 or abs(dy) > 0.5
		if moved and self.editor.settings.cursorTrailEnabled:
			self.cursorTrail.append((self.cursorAnimX, self.cursorAnimY))
			if len(self.cursorTrail) > self.TRAIL_LENGTH:
				self.cursorTrail.pop(0)
		elif self.cursorTrail:
			self.cursorTrail.pop(0)

		needsPaint = scrolled or moved or self.cursorScaleY != 1.0 or bool(self.cursorTrail)
		if moved:
			self.cursorAnimX += dx * speed
			self.cursorAnimY += dy * speed
		elif dx != 0 or dy != 0:
			self.cursorAnimX = float(tx)
			self.cursorAnimY = float(ty)
			needsPaint = True
		if needsPaint:
			self.update()

	def startThemeTransition(self):
		if self.backgroundImage is not None:
			self.previousBackgroundImage = self.backgroundImage.copy()
		else:
			self.previousBackgroundImage = None
		self.transitionProgress = 0.0
		self.transitionElapsed = 0
		self.transitionTimer.start()

	def tickTransition(self):
		self.transitionElapsed += 16
		self.transitionProgress = min(1.0, self.transitionElapsed / self.transitionDuration)
		if self.transitionProgress >= 1.0:
			self.transitionTimer.stop()
			self.previousBackgroundImage = None
		self.update()

	def drawBackground(self, painter):
		from frontend.qt.amigaPalette import palette, buildDitherImage
		gradient 		= palette.get("GRADIENT")
		useDither 		= palette.get("DITHER", False)
		backgroundPath 	= palette.get("BACKGROUND_IMAGE")
		w, h = self.width(), self.height()

		if useDither and gradient:
			if self.backgroundImageSize != (w, h) or self.backgroundImagePath != "gradient":
				self.backgroundImage = buildDitherImage(w, h, gradient)
				self.backgroundImageSize = (w, h)
				self.backgroundImagePath = "gradient"
			newImage = self.backgroundImage
		elif backgroundPath:
			if self.backgroundImagePath != backgroundPath or self.backgroundImage is None:
				self.backgroundImage		= loadBackgroundImage(backgroundPath, w, h)
				self.backgroundImageSize	= (w, h)
				self.backgroundImagePath	= backgroundPath
			if self.backgroundImageSize != (w, h):
				self.resizeDebounce.start()
			newImage = self.backgroundImage
		else:
			self.backgroundImage = None
			self.backgroundImageSize = None
			self.backgroundImagePath = None
			newImage = None

		progress = getattr(self, "transitionProgress", 1.0)
		previousImage = getattr(self, "previousBackgroundImage", None)

		if progress < 1.0 and previousImage is not None:
			painter.setOpacity(1.0 - progress)
			painter.drawImage(self.rect(), previousImage)
			painter.setOpacity(progress)
			if newImage:
				painter.drawImage(self.rect(), newImage)
			else:
				painter.fillRect(self.rect(), QColor(getColor("BACKGROUND")))
			painter.setOpacity(1.0)
			if backgroundPath:
				painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
		else:
			if newImage:
				painter.drawImage(self.rect(), newImage)
				if backgroundPath:
					painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
			else:
				painter.fillRect(self.rect(), QColor(getColor("BACKGROUND")))

	def rebuildBackgroundImage(self):
		from frontend.qt.amigaPalette import palette, loadBackgroundImage
		backgroundPath = palette.get("BACKGROUND_IMAGE")
		if not backgroundPath:
			return
		w, h = self.width(), self.height()
		self.backgroundImage	= loadBackgroundImage(backgroundPath, w, h)
		self.backgroundImageSize = (w, h)
		self.backgroundImagePath = backgroundPath
		self.update()

	def drawGutter(self, painter):
		from frontend.qt.amigaPalette import palette, buildDitherImage
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		pane = self.pane
		gradient = palette.get("GRADIENT")
		useDither = palette.get("DITHER", False)
		backgroundPath = palette.get("BACKGROUND_IMAGE")
		gw, gh = self.gutterWidth, self.height()

		if (useDither and gradient) or backgroundPath:
			if self.backgroundImageSize == (self.width(), gh) and self.backgroundImage is not None:
				painter.drawImage(0, 0, self.backgroundImage, 0, 0, gw, gh)
			else:
				painter.fillRect(0, 0, gw, gh, QColor(getColor("GUTTER")))
			if useDither and gradient:
				painter.fillRect(0, 0, gw, gh, QColor(0, 0, 0, 140))
		else:
			painter.fillRect(0, 0, gw, gh, QColor(getColor("GUTTER")))

		visibleCount = self.height() // lineHeight + 1
		for i in range(visibleCount):
			bufferY = pane.scrollY + i
			if bufferY >= len(pane.buffer.lines):
				break
			isCurrent = (bufferY == pane.cursorY)
			painter.setPen(QColor(getColor("CURRENT_LINE_NUMBER")) if isCurrent else QColor(getColor("LINE_NUMBER")))
			text = str(bufferY + 1)
			textWidth = metrics.horizontalAdvance(text)
			x = self.gutterWidth - textWidth - 10
			y = i * lineHeight + metrics.ascent()
			painter.drawText(x, y, text)

		if self.editor.settings.gitDiffEnabled:
			filepath = pane.buffer.filename
			if filepath != self.diffCacheFile:
				from util.gitDiff import getDiffLines
				self.diffCache = getDiffLines(filepath)
				self.diffCacheFile = filepath
			for i in range(visibleCount):
				bufferY = pane.scrollY + i
				if bufferY >= len(pane.buffer.lines):
					break
				diffType = self.diffCache.get(bufferY + 1)
				if diffType == "added":
					diffColor = QColor("#55FF55")
				elif diffType == "removed":
					diffColor = QColor("#FF5555")
				else:
					diffColor = None
				if diffColor:
					y = i * lineHeight
					painter.fillRect(gw - 2, y, 2, lineHeight, diffColor)

		if self.paneIndex == self.editor.activePane and not getattr(self.editor, "explorerFocused", False):
			painter.fillRect(0, 0, 3, self.height(), QColor(getColor("CURSOR")))

		totalLines = len(pane.buffer.lines)
		if totalLines <= pane.visibleLines:
			return
		metrics		= QFontMetrics(self.font)
		lineHeight	= metrics.height()
		trackHeight	= self.height()
		trackX		= self.gutterWidth - 4
		trackWidth	= 3

		painter.fillRect(trackX, 0, trackWidth, trackHeight, QColor(0, 0, 0, 60))

		thumbRatio	= pane.visibleLines / totalLines
		thumbHeight	= max(12, int(trackHeight * thumbRatio))
		scrollRatio	= pane.scrollY / max(1, totalLines - pane.visibleLines)
		thumbY		= int((trackHeight - thumbHeight) * scrollRatio)

		thumbColor	= QColor(getColor("COMMENT"))
		thumbColor.setAlpha(180)
		painter.fillRect(trackX, thumbY, trackWidth, thumbHeight, thumbColor)

	def drawText(self, painter):
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		charWidth = metrics.horizontalAdvance("M")
		tabSize = max(1, self.editor.settings.tabSize)
		pane = self.pane
		scrollX = pane.scrollX
		visibleCount = self.height() // lineHeight + 1
		lines = pane.buffer.lines[pane.scrollY: pane.scrollY + visibleCount]
		rightEdge = self.width()

		for lineIndex, line in enumerate(lines):
			tokens = self.lexer.tokenize(line, pane.buffer.language)
			baseline = lineIndex * lineHeight + metrics.ascent()
			visualCol = 0
			done = False
			for tokenText, tokenType in tokens:
				painter.setPen(self.tokenColor(tokenType))
				for ch in tokenText:
					width = (tabSize - (visualCol % tabSize)) if ch == "\t" else 1
					if visualCol + width > scrollX and ch != "\t":
						x = self.textX + (visualCol - scrollX) * charWidth
						if x >= rightEdge:
							done = True
							break
						painter.drawText(x, baseline, ch)
					visualCol += width
				if done:
					break

	def drawIndentGuides(self, painter):
		if not self.SHOW_INDENT_GUIDES:
			return
		tabSize = max(1, self.editor.settings.tabSize)
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		charWidth = metrics.horizontalAdvance("M")
		pane = self.pane
		lines = pane.buffer.lines
		color = QColor(getColor("COMMENT"))
		color.setAlpha(60)
		visibleCount = self.height() // lineHeight + 1
		for i in range(visibleCount):
			y = pane.scrollY + i
			if y >= len(lines):
				break
			line = lines[y]
			if not line.strip():
				continue
			visual = 0
			for ch in line:
				if ch == " ":
					visual += 1
				elif ch == "\t":
					visual += tabSize - (visual % tabSize)
				else:
					break
			col = 0
			while col < visual:
				x = self.textX + (col - pane.scrollX) * charWidth
				if x >= self.textX:
					painter.fillRect(x, i * lineHeight, 1, lineHeight, color)
				col += tabSize

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

		languageName = pane.buffer.language.name if pane.buffer.language else None
		cursorColor = QColor(getColorForLanguage("CURSOR", languageName))

		if self.cursorAnimX is None:
			tx, ty = self.cursorPixelPos()
			self.cursorAnimX = float(tx)
			self.cursorAnimY = float(ty)

		for cursor in pane.multiCursor.cursors:
			isPrimary = (cursor is pane.multiCursor.primary)
			visibleY = cursor.y - pane.scrollY
			if visibleY < 0:
				continue
			try:
				line = pane.buffer.lines[cursor.y]
			except IndexError:
				continue
			
			if isPrimary:
				x = int(self.cursorAnimX)
				y = int(self.cursorAnimY)
				scaleY = getattr(self, "cursorScaleY", 1.0)
			else:
				x = self.cursorXToPixel(line, cursor.x)
				y = visibleY * lineHeight
				scaleY = 1.0

			scaledHeight = max(2, int(lineHeight * scaleY))
			yOffset = (lineHeight - scaledHeight) // 2

			painter.fillRect(x, y + yOffset, charWidth, scaledHeight, cursorColor)

			if isPrimary:
				try:
					ch = line[cursor.x]
				except IndexError:
					ch = " "
				if scaleY > 0.6:
					painter.setPen(QColor(getColor("BACKGROUND")))
					painter.drawText(int(x), int(y) + metrics.ascent(), ch)
				self.editor.completionX = x
				self.editor.completionY = y

		for i, (tx, ty) in enumerate(self.cursorTrail):
			alpha = int(160 * (i + 1) / max(len(self.cursorTrail), 1))
			trailColor = QColor(cursorColor)
			trailColor.setAlpha(alpha)
			trailH = max(2, int(lineHeight * (0.3 + 0.7 * (i + 1) / len(self.cursorTrail))))
			trailYOff = (lineHeight - trailH) // 2
			painter.fillRect(int(tx), int(ty) + trailYOff, charWidth, trailH, trailColor)

	def drawCurrentLine(self, painter):
		from frontend.qt.amigaPalette import palette
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		visibleY = self.pane.cursorY - self.pane.scrollY
		if visibleY < 0:
			return
		y = visibleY * lineHeight
		useDither = palette.get("DITHER", False)
		gradient = palette.get("GRADIENT")
		if useDither and gradient:
			painter.fillRect(self.gutterWidth + 1, y, self.width() - self.gutterWidth - 1, lineHeight, QColor(255, 255, 255, 18))
		else:
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

		languageName = pane.buffer.language.name if pane.buffer.language else None
		selectionColor = QColor(getColorForLanguage("SELECTION", languageName))

		def bufferColToVisualCol(line, col):
			visual = 0
			for i, ch in enumerate(line):
				if i >= col:
					break
				if ch == "\t":
					visual += self.editor.settings.tabSize - (visual % self.editor.settings.tabSize)
				else:
					visual += 1
			return visual

		for visibleLine in range(visibleCount):
			bufferY = pane.scrollY + visibleLine
			if bufferY >= len(pane.buffer.lines):
				break
			line = pane.buffer.lines[bufferY]
			for norm in selection.allNormalized():
				if norm["sy"] <= bufferY <= norm["ey"]:
					sc = norm["sx"] if bufferY == norm["sy"] else 0
					ec = norm["ex"] if bufferY == norm["ey"] else len(pane.buffer.lines[bufferY])

					scVisual = bufferColToVisualCol(line, sc)
					ecVisual = bufferColToVisualCol(line, ec)

					x0 = max(self.textX, self.textX + (scVisual - pane.scrollX) * charWidth)
					x1 = self.textX + (ecVisual - pane.scrollX) * charWidth
					if x1 > x0:
						painter.fillRect(x0, visibleLine * lineHeight, x1 - x0, lineHeight, selectionColor)
					painter.setPen(QColor(getColor("SELECTION_TEXT")))
					visualCol = scVisual
					for col in range(sc, min(ec, len(line))):
						if visualCol < pane.scrollX:
							ch = line[col]
							if ch == "\t":
								visualCol += self.editor.settings.tabSize - (visualCol % self.editor.settings.tabSize)
							else:
								visualCol += 1
							continue
						ch = line[col]
						if ch == "\t":
							spaces = self.editor.settings.tabSize - (visualCol % self.editor.settings.tabSize)
							visualCol += spaces
						else:
							cx = self.textX + (visualCol - pane.scrollX) * charWidth
							painter.drawText(cx, visibleLine * lineHeight + metrics.ascent(), ch)
							visualCol += 1

	def tokenColor(self, tokenType):
		mapping = {
			"keyword": "KEYWORD",
			"string": "STRING",
			"comment": "COMMENT",
			"text": "TEXT",
			"number": "NUMBER",
		}
		return QColor(getColor(mapping.get(tokenType, "TEXT")))

	def focusInEvent(self, event):
		super().focusInEvent(event)
		if self.editor.activePane != self.paneIndex:
			self.editor.activePane = self.paneIndex
			self.editor.notifyChanged()

	def modalInputActive(self):
		ed = self.editor
		return bool(
			getattr(ed, "searchMode", False) or getattr(ed, "paletteOpen", False)
			or getattr(ed, "saving", False) or getattr(ed, "gotoMode", False)
			or getattr(ed, "folderInputMode", False)
		)

	def pasteIntoModalInput(self):
		"""Ctrl+V in the search bar / palette / goto / save-as: feed the clipboard in as typed keys."""
		from PyQt6.QtWidgets import QApplication
		from input.event import InputEvent
		lines = QApplication.clipboard().text().splitlines()
		for ch in (lines[0] if lines else ""):
			if ch.isprintable():
				self.editor.handleInput(InputEvent(key=ch, ctrl=False, shift=False, alt=False))
		self.editor.notifyChanged()

	def contextMenuEvent(self, event):
		from PyQt6.QtWidgets import QMenu, QApplication
		from input.event import InputEvent
		self.editor.activePane = self.paneIndex
		menu = QMenu(self)
		cutAction = menu.addAction("Cut")
		copyAction = menu.addAction("Copy")
		pasteAction = menu.addAction("Paste")
		menu.addSeparator()
		selectAllAction = menu.addAction("Select All")
		pasteAction.setEnabled(bool(QApplication.clipboard().text()))
		keys = {cutAction: "X", copyAction: "C", pasteAction: "V", selectAllAction: "A"}
		key = keys.get(menu.exec(event.globalPos()))
		self.setFocus()
		if key:
			self.editor.handleInput(InputEvent(key=key, ctrl=True, shift=False, alt=False))
			self.editor.updateScroll()
			self.editor.notifyChanged()

	def keyPressEvent(self, event):
		self.editor.activePane = self.paneIndex
		mods = event.modifiers()
		ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
		shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
		isPaste = (event.key() == Qt.Key.Key_V and ctrl and not (mods & Qt.KeyboardModifier.AltModifier)) \
			or (event.key() == Qt.Key.Key_Insert and shift and not ctrl)
		if isPaste and self.modalInputActive():
			self.pasteIntoModalInput()
			event.accept()
			return
		inputEvent = translateKey(event)
		bufferBefore = self.pane.buffer
		scrollXBefore = self.pane.scrollX
		self.editor.handleInput(inputEvent)
		self.editor.updateScroll()
		if self.pane.buffer is bufferBefore:
			self.pane.scrollX = scrollXBefore
		self.editor.notifyChanged()
		self.cursorChanged.emit(self.pane.cursorY + 1, self.pane.cursorX + 1)
		event.accept()

	def mousePressEvent(self, event):
		self.setFocus()
		self.editor.activePane = self.paneIndex
		self.editor.completionActive = False
		self.editor.completions = []
		self.editor._undoGroup = None
		if event.button() == Qt.MouseButton.LeftButton:
			row, col = self.pixelToRowCol(event.position().x(), event.position().y())
			modifiers = event.modifiers()
			if modifiers & Qt.KeyboardModifier.AltModifier:
				self.pane.multiCursor.addCursor(col, row)
				self.editor.notifyChanged()
				event.accept()
				return
			if modifiers & Qt.KeyboardModifier.ShiftModifier:
				selection = self.editor.selection
				if not selection.active:
					selection.begin(self.pane.cursorX, self.pane.cursorY)
				selection.update(col, row)
				self.pane.cursorX = col
				self.pane.cursorY = row
				self.mouseSelecting = True
				self.editor.notifyChanged()
				event.accept()
				return
			self.pane.multiCursor.reset(col, row)
			self.editor.selection.clear()
			self.mouseSelecting = True
			self.editor.notifyChanged()
		event.accept()

	def mouseDoubleClickEvent(self, event):
		if event.button() != Qt.MouseButton.LeftButton:
			return
		row, col = self.pixelToRowCol(event.position().x(), event.position().y())
		line = self.pane.buffer.lines[row]
		self.mouseSelecting = False
		if not line:
			return
		col = min(col, len(line) - 1)
		isWord = lambda c: c.isalnum() or c == "_"
		if isWord(line[col]):
			same = isWord
		elif line[col].isspace():
			same = lambda c: c.isspace()
		else:
			same = lambda c: False
		start = col
		while start > 0 and same(line[start - 1]):
			start -= 1
		end = col + 1
		while end < len(line) and same(line[end]):
			end += 1
		selection = self.editor.selection
		selection.clear()
		selection.begin(start, row)
		selection.update(end, row)
		self.pane.cursorX = end
		self.pane.cursorY = row
		self.editor.notifyChanged()
		event.accept()

	def mouseMoveEvent(self, event):
		if self.mouseSelecting and event.buttons() & Qt.MouseButton.LeftButton:
			py = event.position().y()
			if py < 0:
				self.pane.scrollY = max(0, self.pane.scrollY - 1)
			elif py > self.height():
				self.pane.scrollY = min(max(0, len(self.pane.buffer.lines) - 1), self.pane.scrollY + 1)
			row, col = self.pixelToRowCol(event.position().x(), py)
			if not self.editor.selection.active:
				self.editor.selection.begin(self.pane.cursorX, self.pane.cursorY)
			self.editor.selection.update(col, row)
			self.pane.cursorX = col
			self.pane.cursorY = row
			self.editor.notifyChanged()
		event.accept()

	def focusNextPrevChild(self, next):
		return False

	def mouseReleaseEvent(self, event):
		self.mouseSelecting = False
		event.accept()

	def wheelEvent(self, event):
		delta = event.angleDelta()
		dx, dy = delta.x(), delta.y()
		if event.modifiers() & Qt.KeyboardModifier.ShiftModifier and dx == 0:
			dx, dy = dy, 0
		self._wheelX += dx
		self._wheelY += dy
		lines = int(self._wheelY / 40)
		cols = int(self._wheelX / 40)
		if lines:
			self._wheelY -= lines * 40
			maxScroll = max(0, len(self.pane.buffer.lines) - 1)
			self.pane.scrollY = max(0, min(maxScroll, self.pane.scrollY - lines))
		if cols:
			self._wheelX -= cols * 40
			self.pane.scrollX = max(0, min(self.pane.scrollX - cols, self.maxScrollX()))
		if lines or cols:
			self.editor.notifyChanged()
		event.accept()

	def storeCursorScreenPos(self):
		pane = self.pane
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		try:
			line = pane.buffer.lines[pane.cursorY]
		except IndexError:
			line = ""
		x = self.cursorXToPixel(line, pane.cursorX)
		y = (pane.cursorY - pane.scrollY) * lineHeight
		
		from PyQt6.QtCore import QPoint
		globalPoint	= self.mapToGlobal(QPoint(x, y))
		editorView	= self.parent()
		while editorView is not None and not hasattr(editorView, 'overlay'):
			editorView = editorView.parent()
		if editorView is not None:
			localPoint = editorView.mapFromGlobal(globalPoint)
			self.editor.completionX = localPoint.x()
			self.editor.completionY = localPoint.y()

	def cursorXToPixel(self, line: str, cursorX: int) -> int:
		metrics = QFontMetrics(self.font)
		charWidth = metrics.horizontalAdvance("M")
		visualCol = 0
		for i, ch in enumerate(line):
			if i >= cursorX:
				break
			if ch == "\t":
				spaces = self.editor.settings.tabSize - (visualCol % self.editor.settings.tabSize)
				visualCol += spaces
			else:
				visualCol += 1
		return self.textX + (visualCol - self.pane.scrollX) * charWidth

	def pixelToRowCol(self, px, py):
		metrics = QFontMetrics(self.font)
		lineHeight = metrics.height()
		charWidth = metrics.horizontalAdvance("M")
		row = int(py // lineHeight) + self.pane.scrollY
		row = max(0, min(row, len(self.pane.buffer.lines) - 1))

		line = self.pane.buffer.lines[row]
		tabSize = self.editor.settings.tabSize
		visualCol = 0
		for i, ch in enumerate(line):
			width = (tabSize - (visualCol % tabSize)) if ch == "\t" else 1
			left = self.textX + (visualCol - self.pane.scrollX) * charWidth
			if px < left + width * charWidth:
				return row, i
			visualCol += width
		return row, len(line)