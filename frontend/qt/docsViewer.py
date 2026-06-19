import os
import re
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFontMetrics, QFont

from frontend.qt.amigaPalette import getColor

DOCS_ROOT = Path(__file__).resolve().parents[2] / "docs"

def loadDocsPages():
	pages = []
	if not DOCS_ROOT.exists():
		return pages
	for file in sorted(DOCS_ROOT.glob("*.md")):
		title = file.stem
		try:
			with open(file, "r", encoding="utf-8") as f:
				firstLine = f.readline().strip()
				if firstLine.startswith("#"):
					title = firstLine.lstrip("#").strip()
		except Exception:
			pass
		pages.append((title, file))
	return pages

def parseMarkdown(text: str):
	lines = text.split("\n")
	blocks = []
	inCode = False
	codeBuffer = []

	for line in lines:
		stripped = line.rstrip()
		if stripped.startswith("```"):
			if inCode:
				blocks.append(("code", "\n".join(codeBuffer)))
				codeBuffer = []
				inCode = False
			else:
				inCode = True
			continue
		if inCode:
			codeBuffer.append(line)
			continue
		if not stripped:
			blocks.append(("blank", ""))
		elif stripped.startswith("### "):
			blocks.append(("h3", stripped[4:]))
		elif stripped.startswith("## "):
			blocks.append(("h2", stripped[3:]))
		elif stripped.startswith("# "):
			blocks.append(("h1", stripped[2:]))
		elif stripped.startswith("---"):
			blocks.append(("hr", ""))
		elif stripped.startswith("- ") or stripped.startswith("* "):
			blocks.append(("bullet", stripped[2:]))
		else:
			blocks.append(("p", stripped))
	return blocks

class DocsOverlay(QWidget):
	SIDEBAR_WIDTH = 220

	def __init__(self, editor, font: QFont, parent=None):
		super().__init__(parent)
		self.editor = editor
		self.font = font
		self.monoFont = QFont(font)

		self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

		self.pages = loadDocsPages()
		self.currentPageIndex = 0
		self.scrollY = 0
		self.contentBlocks = []

		if self.pages:
			self.loadPage(0)
		
		editor.signals.changed.connect(self.update)

	def loadPage(self, index):
		if not (0 <= index < len(self.pages)):
			return
		self.currentPageIndex = index
		_, filePath = self.pages[index]
		try:
			with open(filePath, "r", encoding="utf-8") as f:
				text = f.read()
			self.contentBlocks = parseMarkdown(text)
		except Exception:
			self.contentBlocks = [("p", "Could not load this page.")]
		self.scrollY = 0
		self.update()

	def show(self):
		self.editor.docsOpen = True
		super().show()
		self.raise_()
		self.setFocus()
		self.update()

	def hide(self):
		self.editor.docsOpen = False
		super().hide()

	def paintEvent(self, event):
		painter				= QPainter(self)
		background			= QColor(getColor("PALETTE_BG"))
		foreground			= QColor(getColor("PALETTE_FG"))
		titleForeground		= QColor(getColor("PALETTE_TITLE"))
		selectBackground	= QColor(getColor("PALETTE_SELECT_BG"))
		selectForeground 	= QColor(getColor("PALETTE_SELECT_FG"))
		hintForeground 		= QColor(getColor("PALETTE_HINT"))

		painter.fillRect(self.rect(), background)

		painter.setPen(QColor(getColor("PALETTE_FG")))
		painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

		metrics = QFontMetrics(self.font)
		rowHeight = metrics.height() + 6

		sidebarWidth = self.SIDEBAR_WIDTH
		painter.fillRect(0, 0, sidebarWidth, self.height(), QColor(0, 0, 0, 40))
		painter.setPen(titleForeground)
		painter.setFont(self.font)
		painter.drawText(12, rowHeight, "DOCUMENTATION")
		painter.setPen(foreground)
		painter.drawLine(8, rowHeight + 8, sidebarWidth - 8, rowHeight + 8)

		y = rowHeight + 8 + 12
		for i, (title, _) in enumerate(self.pages):
			rectY = y + i * rowHeight
			if i == self.currentPageIndex:
				painter.fillRect(4, rectY - 2, sidebarWidth - 8, rowHeight, selectBackground)
				painter.setPen(selectForeground)
			else:
				painter.setPen(foreground)
			label = title.upper()
			maxWidth = sidebarWidth - 24
			while metrics.horizontalAdvance(label) > maxWidth and len(label) > 4:
				label = label[:-4] + "..."
			painter.drawText(12, rectY + metrics.ascent(), label)
		painter.setPen(foreground)
		painter.drawLine(sidebarWidth, 0, sidebarWidth, self.height())

		contentX = sidebarWidth + 24
		contentWidth = self.width() - contentX - 24
		cy = 20 - self.scrollY

		painter.setClipRect(sidebarWidth, 0, self.width() - sidebarWidth, self.height() - 40)
		for kind, text in self.contentBlocks:
			if kind == "h1":
				painter.setFont(QFont(self.font.family(), self.font.pointSize() + 4, QFont.Weight.Bold))
				painter.setPen(titleForeground)
				m = QFontMetrics(painter.font())
				painter.drawText(contentX, cy  + m.ascent(), text)
				cy += m.height() + 14
			elif kind == "h2":
				painter.setFont(QFont(self.font.family(), self.font.pointSize() + 2, QFont.Weight.Bold))
				painter.setPen(titleForeground)
				m = QFontMetrics(painter.font())
				painter.drawText(contentX, cy  + m.ascent(), text)
				cy += m.height() + 10
			elif kind == "h3":
				painter.setFont(QFont(self.font.family(), self.font.pointSize(), QFont.Weight.Bold))
				painter.setPen(titleForeground)
				m = QFontMetrics(painter.font())
				painter.drawText(contentX, cy  + m.ascent(), text)
				cy += m.height() + 8
			elif kind == "code":
				painter.setFont(self.monoFont)
				m = QFontMetrics(self.monoFont)
				codeLines = text.split("\n")
				boxHeight = len(codeLines) * m.height() + 12
				painter.fillRect(contentX, cy, contentWidth, boxHeight, QColor(0, 0, 0, 80))
				painter.setPen(hintForeground)
				innerY = cy + 6
				for line in codeLines:
					painter.drawText(contentX + 10, innerY + m.ascent(), line)
					innerY += m.height()
				cy += boxHeight + 12
			elif kind == "bullet":
				painter.setFont(self.font)
				m = QFontMetrics(self.font)
				painter.setPen(foreground)
				wrapped = self.wraps(text, m, contentWidth - 24)
				for j, wLine in enumerate(wrapped):
					prefix = "* " if j == 0 else "  "
					painter.drawText(contentX + 8, cy + m.ascent(), prefix + wLine)
					cy += m.height() + 2
				cy += 3
			elif kind == "p":
				painter.setFont(self.font)
				m = QFontMetrics(self.font)
				painter.setPen(foreground)
				wrapped = self.wraps(text, m, contentWidth)
				for wLine in wrapped:
					painter.drawText(contentX, cy + m.ascent(), wLine)
					cy += m.height() + 2
				cy += 6
			elif kind == "hr":
				painter.setPen(hintForeground)
				painter.drawLine(contentX, cy + 6, contentX + contentWidth, cy + 6)
				cy += 16
			elif kind == "blank":
				cy += 8

		footerHeight = 36
		footerY = self.height() - footerHeight

		painter.setClipping(False)

		painter.setPen(QColor(getColor("PALETTE_FG")))
		painter.drawLine(0, footerY, self.width(), footerY)

		painter.fillRect(0, footerY + 1, self.width(), footerHeight - 1, QColor(0, 0, 0, 60))

		painter.setPen(QColor(getColor("PALETTE_HINT")))
		painter.setFont(self.font)
		fm = QFontMetrics(self.font)
		hintText = "↑↓ Pages   PGUP/PGDN Scroll   ESC Close"
		textWidth = fm.horizontalAdvance(hintText)
		painter.drawText(self.width() - textWidth -  12, footerY + (footerHeight - fm.height()) // 2 + fm.ascent(), hintText)

	def wraps(self, text, metrics, maxWidth):
		words = text.split(" ")
		lines = []
		current = ""
		for word in words:
			trial = (current + " " + word).strip()
			if metrics.horizontalAdvance(trial) > maxWidth and current:
				lines.append(current)
				current = word
			else:
				current = trial
		if current:
			lines.append(current)
		return lines or [""]
	
	def keyPressEvent(self, event):
		key = event.key()
		if key == Qt.Key.Key_Escape:
			self.hide()
			self.editor.notifyChanged()
			return
		if key == Qt.Key.Key_Up:
			self.loadPage(max(0, self.currentPageIndex - 1))
			return
		if key == Qt.Key.Key_Down:
			self.loadPage(min(len(self.pages) - 1, self.currentPageIndex + 1))
			return
		if key == Qt.Key.Key_PageUp:
			self.scrollY = max(0, self.scrollY - 300)
			self.update()
			return
		if key == Qt.Key.Key_PageDown:
			self.scrollY += 300
			self.update()
			return
		super().keyPressEvent(event)

	def mousePressEvent(self, event):
		pos = event.position().toPoint()
		if pos.x() < self.SIDEBAR_WIDTH:
			metrics = QFontMetrics(self.font)
			rowHeight = metrics.height() + 6
			y = rowHeight + 8 + 12
			for i in range(len(self.pages)):
				rectY = y + i * rowHeight
				if rectY - 2 <= pos.y() <= rectY - 2 + rowHeight:
					self.loadPage(i)
					break
		event.accept()