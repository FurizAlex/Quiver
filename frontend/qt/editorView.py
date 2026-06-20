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
	cursorChanged = pyqtSignal(int, int)
	def __init__(self, editor, pane, font: QFont, paneIndex=0):
		super().__init__()
		self.cursorTrail = []
		self.TRAIL_LENGTH = 4

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

		self.transitionTimer = QTimer()
		self.transitionTimer.setInterval(16)
		self.transitionTimer.timeout.connect(self.tickTransition)
		self.transitionProgress = 1.0
		self.transitionDuration = 300
		self.transitionElapsed = 0
		self.previousBackgroundImage = None

		self.resizeDebounce = QTimer()
		self.resizeDebounce.setSingleShot(True)
		self.resizeDebounce.setInterval(120)
		self.resizeDebounce.timeout.connect(self.rebuildBackgroundImage)

		self.diffCache = {}
		self.diffCacheFile = None

		self.cursorAnimX = None
		self.cursorAnimY = None
		self.cursorTargetX = 0
		self.cursorTargetY = 0
		self.animTimer = QTimer()
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
		textAreaW = self.width() - self.textX
		self.pane.lineHeight = lineHeight
		self.pane.charWidth = charWidth
		self.pane.visibleLines = max(1, self.height() // lineHeight)
		self.pane.visibleCols = max(1, textAreaW // charWidth)

	def paintEvent(self, event):
		try:
			self.updateVisibleDimensions()
			painter = QPainter(self)
			painter.setFont(self.font)
			self.drawBackground(painter)
			self.drawCurrentLine(painter)
			self.drawSelection(painter)
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
		tx, ty = self.cursorPixelPos()
		if self.cursorAnimX is None:
			self.cursorAnimX = float(tx)
			self.cursorAnimY = float(ty)
			self.lastCursorRow = self.pane.cursorY
			self.cursorScaleY = 1.0
			return

		if self.pane.cursorY != self.lastCursorRow:
			self.cursorScaleY = 0.08
			self.lastCursorRow = self.pane.cursorY
			self.cursorTrail.clear()
		
		self.cursorScaleY += (1.0 - self.cursorScaleY) * 0.12
		speed = 0.3
		dx = tx - self.cursorAnimX
		dy = ty - self.cursorAnimY
		moved = abs(dx) > 0.5 or abs(dy) > 0.5
		if moved and self.editor.settings.cursorTrailEnabled:
			self.cursorTrail.append((self.cursorAnimX, self.cursorAnimY))
			if len(self.cursorTrail) > self.TRAIL_LENGTH:
				self.cursorTrail.pop(0)
		else:
			if self.cursorTrail:
				self.cursorTrail.pop(0)
		self.cursorAnimX += dx * speed
		self.cursorAnimY += dy * speed
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
			painter.fillRect(0, 0, gw, gh, QColor(0, 0, 0, 140))
		else:
			painter.fillRect(0, 0, gw, gh, QColor(getColor("GUTTER")))

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
					diffColor = QColor("#55FF55")
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
		pane = self.pane
		visibleCount = self.height() // lineHeight + 1
		lines = pane.buffer.lines[pane.scrollY: pane.scrollY + visibleCount]

		for lineIndex, line in enumerate(lines):
			tokens = self.lexer.tokenize(line, pane.buffer.language)
			x = self.textX
			bufferX = 0
			for tokenText, tokenType in tokens:
				for ch in tokenText:
					if bufferX < pane.scrollX:
						bufferX += 1
						continue
					if ch == "\t":
						spaces = self.editor.settings.tabSize - (bufferX % self.editor.settings.tabSize)
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

		if self.cursorAnimX is None:
			tx, ty = self.cursorPixelPos()
			self.cursorAnimX = float(tx)
			self.cursorAnimY = float(ty)

		visibleY = pane.cursorY - pane.scrollY
		if visibleY < 0:
			return
	
		scaleY = getattr(self, "cursorScaleY", 1.0)
		scaledH = max(2, int(lineHeight * scaleY))
		yOffset = (lineHeight - scaledH) // 2

		x = int(self.cursorAnimX)
		y = int(self.cursorAnimY)

		languageName = pane.buffer.language.name if pane.buffer.language else None
		cursorColor = QColor(getColorForLanguage("CURSOR", languageName))
		for i, (tx, ty) in enumerate(self.cursorTrail):
			alpha = int(160 * (i + 1) / max(len(self.cursorTrail), 1))
			trailColor = QColor(cursorColor)
			trailColor.setAlpha(alpha)
			trailH = max(2, int(lineHeight * (0.3 + 0.7 * (i + 1) / len(self.cursorTrail))))
			trailYOff = (lineHeight - trailH) // 2
			painter.fillRect(int(tx), int(ty) + trailYOff, charWidth, trailH, trailColor)

		painter.fillRect(x, y + yOffset, charWidth, scaledH, cursorColor)
		try:
			ch = pane.buffer.lines[pane.cursorY][pane.cursorX]
		except IndexError:
			ch = " "
		if scaleY > 0.6:
			painter.setPen(QColor(getColor("BACKGROUND")))
			painter.drawText(x, y + metrics.ascent(), ch)
		self.editor.completionX = x
		self.editor.completionY = y

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

					x = self.textX + (scVisual - pane.scrollX) * charWidth
					w = (ecVisual - scVisual) * charWidth
					painter.fillRect(x, visibleLine * lineHeight, w, lineHeight, selectionColor)
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

	def keyPressEvent(self, event):
		if event.key() == Qt.Key.Key_Tab:
			self.editor.activePane = self.paneIndex
			inputEvent = translateKey(event)
			self.editor.handleInput(inputEvent)
			self.editor.updateScroll()
			self.editor.notifyChanged()
			event.accept()
			return
		self.editor.activePane = self.paneIndex
		inputEvent = translateKey(event)
		self.editor.handleInput(inputEvent)
		self.editor.updateScroll()
		self.editor.notifyChanged()
		self.cursorChanged.emit(self.pane.cursorY + 1, self.pane.cursorX + 1)

	def mousePressEvent(self, event):
		self.setFocus()
		self.editor.activePane = self.paneIndex
		if event.button() == Qt.MouseButton.LeftButton:
			row, col = self.pixelToRowCol(event.position().x(), event.position().y())
			self.pane.cursorY = row
			self.pane.cursorX = col
			self.editor.selection.clear()

			self.mouseSelecting = True
			self.editor.notifyChanged()
		event.accept()

	def mouseMoveEvent(self, event):
		if getattr(self, 'mouseSelecting', False) and event.buttons() & Qt.MouseButton.LeftButton:
			row, col = self.pixelToRowCol(event.position().x(), event.position().y())
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
		shift = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
		if shift:
			amount = delta.y()
			cols = max(1, abs(amount) // 40)
			if amount > 0:
				self.pane.scrollX = max(0, self.pane.scrollX - cols)
			else:
				self.pane.scrollX = max(0, self.pane.scrollX + cols)
		else:
			if delta.y() != 0:
				lines = max(1, abs(delta.y()) // 40)
				if delta.y() > 0:
					self.pane.scrollY = max(0, self.pane.scrollY - lines)
				else:
					maxScroll = (max(0, len(self.pane.buffer.lines) - 1))
					self.pane.scrollY = min(maxScroll, self.pane.scrollY + lines)
				if delta.x() != 0:
					cols = max(1, abs(delta.x()) // 40)
					if delta.x() > 0:
						self.pane.scrollX = max(0, self.pane.scrollX - cols)
					else:
						self.pane.scrollX = self.pane.scrollX + cols
		self.editor.notifyChanged()

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
		row = int(py / lineHeight) + self.pane.scrollY
		row = max(0, min(row, len(self.pane.buffer.lines) - 1))

		line = self.pane.buffer.lines[row]
		visualCol = 0
		for i, ch in enumerate(line):
			pixelX = self.textX + (visualCol - self.pane.scrollX) * charWidth
			if pixelX >= px:
				return row, i
			if ch == "\t":
				spaces = self.editor.settings.tabSize - (visualCol % self.editor.settings.tabSize)
				visualCol += spaces
			else:
				visualCol += 1
		return row, len(line)