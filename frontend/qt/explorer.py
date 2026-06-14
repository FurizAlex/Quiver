import os
from commands.fileCommands import openFileBuffer
from PyQt6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QColor

from frontend.qt.amigaPalette import getColor

class ExplorerHeader(QWidget):
	def __init__(self, editor, font: QFont):
		super().__init__()
		self.editor = editor
		self.font = font
		metrics = QFontMetrics(font)
		self.rowHeight = metrics.height() + 4
		self.setFixedHeight(self.rowHeight * 2)
		editor.signals.changed.connect(self.update)

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setFont(self.font)
		metrics = QFontMetrics(self.font)

		explorerBg = getColor("EXPLORER_BG")
		explorerFg = getColor("EXPLORER_FG")
		selectBg = getColor("EXPLORER_SELECT_BG")
		selectFg = getColor("EXPLORER_SELECT_FG")

		painter.fillRect(self.rect(), QColor(explorerBg))
		buffer = self.editor.pane.buffer
		name = buffer.name.upper()
		if buffer.modified:
			name += " *"

		textWidth = metrics.horizontalAdvance(name)
		boxX, boxY = 4, 2
		painter.fillRect(boxX, boxY, textWidth + 8, self.rowHeight - 4, QColor(selectBg))
		painter.setPen(QColor(selectFg))
		painter.drawText(boxX + 4, boxY + metrics.ascent(), name)

		painter.setPen(QColor(explorerFg))
		painter.drawText(6, self.rowHeight + metrics.ascent() + 2, "FILES")

class Explorer(QWidget):
	def __init__(self, editor, font: QFont):
		super().__init__()
		self.editor = editor
		self.font = font
		self.setObjectName("explorerPanel")
		self.setFixedWidth(240)

		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		self.header = ExplorerHeader(editor, font)

		self.backButton = QPushButton("← ..")
		self.backButton.setFont(font)
		self.backButton.setFixedHeight(QFontMetrics(font).height() + 4)
		self.backButton.setStyleSheet(
			"QPushButton { background: #0000AA; color: white; "
			"border: none; border-bottom: 1px solid #3333AA; "
			"text-align: left; padding-left: 6px; }"
			"QPushButton:hover { background: #0000CC; }"
		)
		self.backButton.clicked.connect(self.goBack)

		self.listWidget = QListWidget()
		self.listWidget.setObjectName("explorer")
		self.listWidget.setFont(font)
		self.listWidget.setStyleSheet(
			"QListWidget { background: #0000AA; color: white; border: none; outline: none; }"
			"QListWidget::item { background: #0000AA; color: white; padding: 1px 4px; }"
			"QListWidget::item:selected { background: white; color: #0000AA; }"
			"QListWidget::item:hover { background: #0000CC; color: white; }"
		)
		self.listWidget.viewport().setStyleSheet("background: #0000AA;")
		self.listWidget.itemClicked.connect(self.openSelectedFile)
		self.listWidget.installEventFilter(self)

		layout.addWidget(self.header)
		layout.addWidget(self.backButton)
		layout.addWidget(self.listWidget, stretch=1)

		editor.signals.changed.connect(self.syncVisibility)
		editor.signals.changed.connect(self.updateStyle)
		self.updateStyle()
		self.syncVisibility()

	def updateStyle(self):
		explorerBg = getColor("EXPLORER_BG")
		explorerFg = getColor("EXPLORER_FG")
		selectBg   = getColor("EXPLORER_SELECT_BG")
		selectFg   = getColor("EXPLORER_SELECT_FG")
		self.backButton.setStyleSheet(
		    "QPushButton { background: " + explorerBg + "; color: " + explorerFg + "; "
		    "border: none; border-bottom: 1px solid " + selectBg + "; "
		    "text-align: left; padding-left: 6px; }"
		    "QPushButton:hover { background: " + selectBg + "; color: " + selectFg + "; }"
		)
		self.listWidget.setStyleSheet(
		    "QListWidget { background: " + explorerBg + "; color: " + explorerFg + "; "
		    "border: none; outline: none; }"
		    "QListWidget::item { background: " + explorerBg + "; color: " + explorerFg + "; "
		    "padding: 1px 4px; }"
		    "QListWidget::item:selected { background: " + selectBg + "; color: " + selectFg + "; }"
		    "QListWidget::item:hover { background: " + selectBg + "; color: " + selectFg + "; }"
		)
		self.listWidget.viewport().setStyleSheet(
		    "background: " + explorerBg + ";"
		)

	def syncVisibility(self):
		self.setVisible(self.editor.showExplorer)

	def goBack(self):
		parent = os.path.dirname(os.path.abspath(self.editor.explorerPath))
		if parent != os.path.abspath(self.editor.explorerPath):
			self.editor.explorerPath = parent
			self.rebuild()
			self.editor.notifyChanged()

	def rebuild(self):
		self.listWidget.clear()
		path = self.editor.explorerPath
		try:
			for name in sorted(os.listdir(path)):
				fullPath = os.path.join(path, name)
				label = f"> {name}" if os.path.isdir(fullPath) else f"- {name}"
				item = QListWidgetItem(label)
				item.setData(Qt.ItemDataRole.UserRole, name)
				self.listWidget.addItem(item)
		except Exception:
			pass

	def openSelectedFile(self, item):
		name = item.data(Qt.ItemDataRole.UserRole)
		filepath = os.path.join(self.editor.explorerPath, name)
		if os.path.isdir(filepath):
			self.editor.explorerPath = filepath
			self.rebuild()
		else:
			openFileBuffer(self.editor, filepath)
			self.editor.notifyChanged()

	def eventFilter(self, obj, event):
		from PyQt6.QtCore import QEvent
		from PyQt6.QtGui import QKeyEvent
		if obj is self.listWidget and event.type() == QEvent.Type.KeyPress:
			key = event.key()
			from PyQt6.QtCore import Qt
			if key == Qt.Key.Key_Escape or key == Qt.Key.Key_Tab:
				if hasattr(self, "returnFocusTarget"):
					self.returnFocusTarget.setFocus()
				return True
			if key == Qt.Key.Key_Backspace:
				self.goBack()
				return True
			if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
				item = self.listWidget.currentItem()
				if item:
					self.openSelectedFile(item)
				return True
		return False