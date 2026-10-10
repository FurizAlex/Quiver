import os

from PyQt6.QtWidgets import QWidget, QMenu, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QColor

from frontend.qt.amigaPalette import getColor
from commands.tabCommands import (
	activeIndex, switchToBuffer, moveBuffer, removeBuffer, saveBufferToDisk,
)


class TabBar(QWidget):
	MAX_TEXT_CHARS = 22
	PADDING = 8
	GAP = 2
	DRAG_THRESHOLD = 5

	def __init__(self, editor, font: QFont):
		super().__init__()
		self.editor = editor
		self.font = font
		metrics = QFontMetrics(font)
		self.charWidth = metrics.horizontalAdvance("M")
		self.setFixedHeight(metrics.height() + 8)
		self.setMouseTracking(True)

		self.tabRects = []
		self.plusX = 0
		self.plusW = self.charWidth + 16
		self.contentWidth = 0
		self.scrollX = 0

		self.dragIndex = -1
		self.pressX = 0
		self.dragging = False
		self.hoverIndex = -1
		self.hoverClose = False

		self.lastShown = (-2, -1, -1)
		editor.signals.changed.connect(self.update)

	# ---------- layout ----------

	def tabLabels(self):
		buffers = self.editor.buffers
		names = [(b.name or "UNTITLED").upper() for b in buffers]
		counts = {}
		for name in names:
			counts[name] = counts.get(name, 0) + 1
		labels = []
		for buffer, name in zip(buffers, names):
			if counts[name] > 1 and buffer.filename:
				folder = os.path.basename(os.path.dirname(os.path.abspath(buffer.filename)))
				name = f"{name} ({folder.upper()})"
			labels.append(name)
		return labels

	def closeSlotWidth(self):
		return self.charWidth + 8

	def layoutTabs(self):
		metrics = QFontMetrics(self.font)
		maxText = self.charWidth * self.MAX_TEXT_CHARS
		self.tabRects = []
		x = 4
		for i, label in enumerate(self.tabLabels()):
			shown = metrics.elidedText(label, Qt.TextElideMode.ElideMiddle, maxText)
			w = self.PADDING + metrics.horizontalAdvance(shown) + self.PADDING + self.closeSlotWidth() + 2
			self.tabRects.append((x, w, i, shown))
			x += w + self.GAP
		self.plusX = x
		self.contentWidth = x + self.plusW + 4
		self.clampScroll()

	def clampScroll(self):
		maxScroll = max(0, self.contentWidth - self.width())
		self.scrollX = max(0, min(self.scrollX, maxScroll))

	def revealTab(self, index):
		for x, w, i, _ in self.tabRects:
			if i == index:
				if x - 4 < self.scrollX:
					self.scrollX = max(0, x - 4)
				elif x + w + 4 > self.scrollX + self.width():
					self.scrollX = x + w + 4 - self.width()
		self.clampScroll()

	def tabAt(self, contentX):
		for x, w, i, _ in self.tabRects:
			if x <= contentX < x + w:
				return i
		return -1

	def closeHit(self, index, contentX):
		for x, w, i, _ in self.tabRects:
			if i == index:
				return contentX >= x + w - self.closeSlotWidth() - 2
		return False

	def plusHit(self, contentX):
		return self.plusX <= contentX < self.plusX + self.plusW

	# ---------- painting ----------

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)

		tabBg = getColor("TAB_BG")
		tabFg = getColor("TAB_FG")
		activeBg = getColor("TAB_ACTIVE_BG")
		activeFg = getColor("TAB_ACTIVE_FG")
		accent = getColor("PALETTE_TITLE")

		painter.fillRect(self.rect(), QColor(tabBg))
		self.layoutTabs()

		active = activeIndex(self.editor)
		state = (active, len(self.editor.buffers), self.width())
		if state != self.lastShown:
			self.lastShown = state
			self.revealTab(active)

		h = self.height()
		painter.save()
		painter.translate(-self.scrollX, 0)
		for x, w, i, shown in self.tabRects:
			buffer = self.editor.buffers[i]
			isActive = (i == active)
			isHover = (i == self.hoverIndex)

			if isActive:
				painter.fillRect(x, 0, w, h, QColor(activeBg))
				painter.fillRect(x, h - 2, w, 2, QColor(accent))
				painter.setPen(QColor(activeFg))
			else:
				painter.fillRect(x, 2, w, h - 2, QColor(tabBg))
				if isHover:
					painter.fillRect(x, 2, w, h - 2, QColor(255, 255, 255, 28))
				painter.setPen(QColor(tabFg))
			painter.drawText(x + self.PADDING, metrics.ascent() + 4, shown)

			overClose = isHover and self.hoverClose
			if buffer.modified and not overClose:
				glyph = "*"
			elif isActive or isHover:
				glyph = "x"
			else:
				glyph = ""
			slotX = x + w - self.closeSlotWidth() - 2
			if overClose:
				painter.fillRect(slotX, 3, self.closeSlotWidth(), h - 6, QColor(255, 255, 255, 60))
			if glyph:
				glyphX = slotX + (self.closeSlotWidth() - metrics.horizontalAdvance(glyph)) // 2
				painter.drawText(glyphX, metrics.ascent() + 4, glyph)

		# "+" new tab button
		painter.setPen(QColor(tabFg))
		plusGlyphX = self.plusX + (self.plusW - metrics.horizontalAdvance("+")) // 2
		painter.drawText(plusGlyphX, metrics.ascent() + 4, "+")
		painter.restore()

		# overflow markers
		maxScroll = max(0, self.contentWidth - self.width())
		markW = self.charWidth + 6
		painter.setPen(QColor(accent))
		if self.scrollX > 0:
			painter.fillRect(0, 0, markW, h, QColor(tabBg))
			painter.drawText(3, metrics.ascent() + 4, "<")
		if self.scrollX < maxScroll:
			painter.fillRect(self.width() - markW, 0, markW, h, QColor(tabBg))
			painter.drawText(self.width() - markW + 3, metrics.ascent() + 4, ">")

	# ---------- helpers ----------

	def focusEditor(self):
		views = getattr(self.window(), "views", None)
		if views is None:
			return
		panes = views.paneContainer.paneViews
		index = self.editor.activePane
		if panes and 0 <= index < len(panes):
			panes[index].setFocus()

	def newTab(self):
		window = self.window()
		if hasattr(window, "newFileQt"):
			window.newFileQt()
		self.focusEditor()

	def indexOfBuffer(self, buffer):
		for i, b in enumerate(self.editor.buffers):
			if b is buffer:
				return i
		return -1

	# ---------- mouse ----------

	def mousePressEvent(self, event):
		self.layoutTabs()
		contentX = event.position().x() + self.scrollX
		index = self.tabAt(contentX)
		button = event.button()
		if button == Qt.MouseButton.LeftButton:
			if self.plusHit(contentX):
				self.newTab()
				return
			if index == -1:
				return
			if self.closeHit(index, contentX):
				self.closeTab(index)
				return
			self.dragIndex = index
			self.pressX = event.position().x()
			self.dragging = False
			switchToBuffer(self.editor, index)
			self.focusEditor()
		elif button == Qt.MouseButton.MiddleButton and index != -1:
			self.closeTab(index)

	def mouseMoveEvent(self, event):
		self.layoutTabs()
		x = event.position().x()
		contentX = x + self.scrollX

		if self.dragIndex != -1 and (event.buttons() & Qt.MouseButton.LeftButton):
			if not self.dragging:
				if abs(x - self.pressX) < self.DRAG_THRESHOLD:
					return
				self.dragging = True
				self.setCursor(Qt.CursorShape.ClosedHandCursor)
			i = self.dragIndex
			if i + 1 < len(self.tabRects):
				nx, nw, _, _ = self.tabRects[i + 1]
				if contentX > nx + nw / 2:
					moveBuffer(self.editor, i, i + 1)
					self.dragIndex = i + 1
					return
			if i > 0:
				px, pw, _, _ = self.tabRects[i - 1]
				if contentX < px + pw / 2:
					moveBuffer(self.editor, i, i - 1)
					self.dragIndex = i - 1
			return

		index = self.tabAt(contentX)
		onClose = index != -1 and self.closeHit(index, contentX)
		if (index, onClose) != (self.hoverIndex, self.hoverClose):
			if index != self.hoverIndex:
				if index == -1:
					self.setToolTip("")
				else:
					buffer = self.editor.buffers[index]
					self.setToolTip(buffer.filename or buffer.name or "Unsaved buffer")
			self.hoverIndex, self.hoverClose = index, onClose
			self.update()

	def leaveEvent(self, event):
		self.hoverIndex = -1
		self.hoverClose = False
		self.update()

	def mouseReleaseEvent(self, event):
		self.dragIndex = -1
		self.dragging = False
		self.unsetCursor()

	def mouseDoubleClickEvent(self, event):
		self.layoutTabs()
		contentX = event.position().x() + self.scrollX
		if self.tabAt(contentX) == -1 and not self.plusHit(contentX):
			self.newTab()

	def wheelEvent(self, event):
		delta = event.angleDelta().y() or event.angleDelta().x()
		self.scrollX -= delta
		self.clampScroll()
		self.update()

	def contextMenuEvent(self, event):
		self.layoutTabs()
		index = self.tabAt(event.pos().x() + self.scrollX)
		if index == -1:
			return
		buffers = self.editor.buffers
		target = buffers[index]
		menu = QMenu(self)
		closeAction = menu.addAction("Close")
		othersAction = menu.addAction("Close Others")
		rightAction = menu.addAction("Close to the Right")
		allAction = menu.addAction("Close All")
		menu.addSeparator()
		pathAction = menu.addAction("Copy Path")
		pathAction.setEnabled(bool(target.filename))
		othersAction.setEnabled(len(buffers) > 1)
		rightAction.setEnabled(index < len(buffers) - 1)

		chosen = menu.exec(event.globalPos())
		if chosen is None:
			return
		if chosen == closeAction:
			self.closeTab(index)
		elif chosen == othersAction:
			switchToBuffer(self.editor, index)
			self.closeMany([b for b in buffers if b is not target])
		elif chosen == rightAction:
			self.closeMany(list(buffers[index + 1:]))
		elif chosen == allAction:
			self.closeMany(list(buffers))
		elif chosen == pathAction:
			QApplication.clipboard().setText(os.path.abspath(target.filename))
		self.focusEditor()

	# ---------- closing ----------

	def closeMany(self, targets):
		for buffer in targets:
			index = self.indexOfBuffer(buffer)
			if index == -1:
				continue
			if not self.closeTab(index):
				return False
		return True

	def closeTab(self, index):
		buffers = self.editor.buffers
		if not (0 <= index < len(buffers)):
			return False
		buffer = buffers[index]
		if buffer.modified:
			from frontend.qt.app import QuiverDialog
			outcome = QuiverDialog.ask(
				"UNSAVED CHANGES",
				f"'{buffer.name}' has unsaved changes.\n\n"
				"YES  closes without saving\n"
				"YES + SAVE  saves, then closes\n"
				"NO  keeps it open",
				self.font,
				self.window(),
				showSave=True
			)
			if outcome == "save":
				if not saveBufferToDisk(self.editor, buffer, self.window()):
					return False
			elif outcome != "yes":
				return False
		removeBuffer(self.editor, index)
		self.focusEditor()
		return True
