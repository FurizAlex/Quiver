import os
import shutil
import time

from PyQt6.QtWidgets import (
	QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
	QPushButton, QInputDialog, QMenu, QApplication,
)
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QColor

from commands.fileCommands import openFileBuffer
from commands.tabCommands import buffersUnder, removeBuffer, flash
from frontend.qt.amigaPalette import getColor

IGNORED_NAMES = {".git", "__pycache__", ".DS_Store"}
KEEP = object()


def listDirectory(path):
	"""Folders first, then files, case-insensitive. Same order is used by rebuild + autoRefresh."""
	try:
		names = os.listdir(path)
	except OSError:
		return []
	names = [n for n in names if n not in IGNORED_NAMES and not n.endswith(".pyc")]
	names.sort(key=lambda n: (not os.path.isdir(os.path.join(path, n)), n.lower()))
	return names


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
		name = (buffer.name or "UNTITLED").upper()
		if buffer.modified:
			name += " *"
		name = metrics.elidedText(name, Qt.TextElideMode.ElideMiddle, self.width() - 24)

		textWidth = metrics.horizontalAdvance(name)
		boxX, boxY = 4, 2
		painter.fillRect(boxX, boxY, textWidth + 8, self.rowHeight - 4, QColor(selectBg))
		painter.setPen(QColor(selectFg))
		painter.drawText(boxX + 4, boxY + metrics.ascent(), name)

		path = getattr(self.editor, "explorerPath", None) or ""
		folder = os.path.basename(path.rstrip("/\\")) or path
		label = metrics.elidedText("FILES: " + folder.upper(), Qt.TextElideMode.ElideRight, self.width() - 12)
		painter.setPen(QColor(explorerFg))
		painter.drawText(6, self.rowHeight + metrics.ascent() + 2, label)

		if self.editor.showExplorer and getattr(self.editor, "explorerFocused", False):
			painter.fillRect(0, self.height() - 2, self.width(), 2, QColor(getColor("PALETTE_TITLE")))


class Explorer(QWidget):
	def __init__(self, editor, font: QFont):
		super().__init__()
		self.editor = editor
		self.font = font
		self.names = []
		self.typeBuffer = ""
		self.typeTime = 0.0
		self.setObjectName("explorerPanel")
		self.setMinimumWidth(160)
		self.setMaximumWidth(560)
		self.resize(240, self.height())

		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		self.header = ExplorerHeader(editor, font)

		metrics = QFontMetrics(font)
		buttonH = metrics.height() + 4

		self.backButton = QPushButton("← ..")
		self.backButton.setFont(font)
		self.backButton.setFixedHeight(buttonH)
		self.backButton.clicked.connect(self.goBack)

		self.newFileButton = QPushButton("+ FILE")
		self.newFileButton.setFont(font)
		self.newFileButton.setFixedHeight(buttonH)
		self.newFileButton.setFixedWidth(metrics.horizontalAdvance("+ FILE") + 20)
		self.newFileButton.clicked.connect(self.createFile)

		self.newFolderButton = QPushButton("+ DIR")
		self.newFolderButton.setFont(font)
		self.newFolderButton.setFixedHeight(buttonH)
		self.newFolderButton.setFixedWidth(metrics.horizontalAdvance("+ DIR") + 20)
		self.newFolderButton.clicked.connect(self.createFolder)

		buttonRowWidget = QWidget()
		buttonRowWidget.setFixedHeight(buttonH)
		buttonRowLayout = QHBoxLayout(buttonRowWidget)
		buttonRowLayout.setContentsMargins(0, 0, 0, 0)
		buttonRowLayout.setSpacing(0)
		buttonRowLayout.addWidget(self.backButton, stretch=1)
		buttonRowLayout.addWidget(self.newFileButton)
		buttonRowLayout.addWidget(self.newFolderButton)

		self.listWidget = QListWidget()
		self.listWidget.setObjectName("explorer")
		self.listWidget.setFont(font)
		self.listWidget.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
		self.listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
		self.listWidget.customContextMenuRequested.connect(self.showContextMenu)
		self.listWidget.itemClicked.connect(self.openSelectedFile)
		self.listWidget.installEventFilter(self)

		layout.addWidget(self.header)
		layout.addWidget(buttonRowWidget)
		layout.addWidget(self.listWidget, stretch=1)

		self.refreshTimer = QTimer(self)
		self.refreshTimer.setInterval(2000)
		self.refreshTimer.timeout.connect(self.autoRefresh)
		self.refreshTimer.start()

		editor.signals.changed.connect(self.syncVisibility)
		editor.signals.changed.connect(self.updateStyle)
		for button in (self.backButton, self.newFileButton, self.newFolderButton):
			button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
		self.updateStyle()
		self.syncVisibility()

	# ---------- styling / visibility ----------

	def updateStyle(self):
		explorerBg = getColor("EXPLORER_BG")
		explorerFg = getColor("EXPLORER_FG")
		selectBg = getColor("EXPLORER_SELECT_BG")
		selectFg = getColor("EXPLORER_SELECT_FG")
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
		self.listWidget.viewport().setStyleSheet("background: " + explorerBg + ";")
		buttonStyle = (
			"QPushButton { background: " + selectBg + "; color: " + selectFg + "; "
			"border: none; padding-left: 6px; }"
			"QPushButton:hover { background: " + explorerFg + "; color: " + explorerBg + "; }"
		)
		self.newFileButton.setStyleSheet(buttonStyle)
		self.newFolderButton.setStyleSheet(buttonStyle)

	def syncVisibility(self):
		self.setVisible(self.editor.showExplorer)

	# ---------- listing ----------

	def rebuild(self, select=KEEP):
		"""Rebuild the list. By default the current selection is kept (by name);
		pass a name to select it, or None for the first row."""
		if select is KEEP:
			item = self.listWidget.currentItem()
			select = item.data(Qt.ItemDataRole.UserRole) if item else None
		path = self.editor.explorerPath
		self.names = listDirectory(path) if path else []
		self.listWidget.clear()
		for name in self.names:
			fullPath = os.path.join(path, name)
			label = f"> {name}" if os.path.isdir(fullPath) else f"- {name}"
			item = QListWidgetItem(label)
			item.setData(Qt.ItemDataRole.UserRole, name)
			self.listWidget.addItem(item)
		if self.names:
			row = self.names.index(select) if select in self.names else 0
			self.listWidget.setCurrentRow(row)

	def autoRefresh(self):
		if not self.isVisible() or not self.editor.explorerPath:
			return
		if listDirectory(self.editor.explorerPath) != self.names:
			self.rebuild()

	# ---------- navigation ----------

	def goBack(self):
		current = os.path.abspath(self.editor.explorerPath)
		parent = os.path.dirname(current)
		if parent != current:
			self.editor.setExplorerPath(parent)
			self.rebuild(select=os.path.basename(current))
			self.editor.notifyChanged()

	def openSelectedFile(self, item):
		name = item.data(Qt.ItemDataRole.UserRole)
		filepath = os.path.join(self.editor.explorerPath, name)
		if os.path.isdir(filepath):
			self.editor.setExplorerPath(filepath)
			self.rebuild(select=None)
			self.editor.notifyChanged()
		elif self.openFileSafely(filepath):
			self.returnToEditor()

	def openFileSafely(self, filepath):
		"""Open a file as a tab. Binary / non-UTF-8 files are refused with a message instead of crashing."""
		name = os.path.basename(filepath)
		try:
			with open(filepath, "rb") as f:
				sample = f.read(8192)
			if b"\0" in sample:
				self.say(f"Can't open '{name}': binary file")
				return False
			openFileBuffer(self.editor, filepath)
		except UnicodeDecodeError:
			self.say(f"Can't open '{name}': not a UTF-8 text file")
			return False
		except Exception as e:
			self.say(f"Can't open '{name}': {e}")
			return False
		if not self.editor.pane.buffer.lines:
			self.editor.pane.buffer.lines.append("")
		self.editor.notifyChanged()
		return True

	def focusExplorer(self):
		self.listWidget.setFocus()
		if self.listWidget.count() > 0 and self.listWidget.currentRow() == -1:
			self.listWidget.setCurrentRow(0)

	def returnToEditor(self):
		window = getattr(self.editor, "qtWindow", None) or self.window()
		views = getattr(window, "views", None)
		if views is None:
			for widget in QApplication.topLevelWidgets():
				if hasattr(widget, "views"):
					views = widget.views
					break
		if views is None:
			return
		panes = views.paneContainer.paneViews
		index = self.editor.activePane
		if panes and 0 <= index < len(panes):
			panes[index].setFocus()

	def typeAhead(self, text):
		now = time.monotonic()
		if now - self.typeTime > 0.8:
			self.typeBuffer = ""
		self.typeTime = now
		self.typeBuffer += text.lower()
		for row, name in enumerate(self.names):
			if name.lower().startswith(self.typeBuffer):
				self.listWidget.setCurrentRow(row)
				return

	def eventFilter(self, obj, event):
		if obj is self.listWidget:
			if event.type() == QEvent.Type.FocusIn:
				self.editor.explorerFocused = True
				self.editor.notifyChanged()
				return False
			if event.type() == QEvent.Type.FocusOut:
				self.editor.explorerFocused = False
				self.editor.notifyChanged()
				return False
			if event.type() == QEvent.Type.KeyPress:
				key = event.key()
				mods = event.modifiers()
				ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
				shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
				alt = bool(mods & Qt.KeyboardModifier.AltModifier)
				if key in (Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
					self.returnToEditor()
					return True
				if key in (Qt.Key.Key_Backspace, Qt.Key.Key_Left):
					self.goBack()
					return True
				if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Right):
					item = self.listWidget.currentItem()
					if item:
						self.openSelectedFile(item)
					return True
				if key == Qt.Key.Key_N and ctrl:
					if shift:
						self.createFolder()
					else:
						self.createFile()
					return True
				if key == Qt.Key.Key_F2:
					self.renameSelected()
					return True
				if key == Qt.Key.Key_Delete:
					self.deleteSelected()
					return True
				if key == Qt.Key.Key_F5:
					self.rebuild()
					return True
				text = event.text()
				if text and text.isprintable() and not text.isspace() and not ctrl and not alt:
					self.typeAhead(text)
					return True
		return False

	# ---------- file operations ----------

	def say(self, message):
		flash(self.editor, message)

	@staticmethod
	def validName(name):
		return bool(name) and name not in (".", "..") and not any(c in name for c in "/\\")

	def promptName(self, title, label, default=""):
		name, ok = QInputDialog.getText(self.window(), title, label, text=default)
		name = name.strip()
		if not ok or not name:
			return None
		if not self.validName(name):
			self.say(f"Invalid name: {name}")
			return None
		return name

	def createFile(self):
		name = self.promptName("New File", "File name:")
		if not name:
			return
		path = os.path.join(self.editor.explorerPath, name)
		if os.path.exists(path):
			self.say(f"'{name}' already exists")
			return
		try:
			open(path, "x").close()
		except OSError as e:
			self.say(f"Could not create file: {e}")
			return
		self.rebuild(select=name)
		if self.openFileSafely(path):
			self.returnToEditor()

	def createFolder(self):
		name = self.promptName("New Folder", "Folder name:")
		if not name:
			return
		path = os.path.join(self.editor.explorerPath, name)
		if os.path.exists(path):
			self.say(f"'{name}' already exists")
			return
		try:
			os.makedirs(path)
		except OSError as e:
			self.say(f"Could not create folder: {e}")
			return
		self.rebuild(select=name)
		self.editor.notifyChanged()

	def renameSelected(self):
		item = self.listWidget.currentItem()
		if not item:
			return
		oldName = item.data(Qt.ItemDataRole.UserRole)
		oldPath = os.path.join(self.editor.explorerPath, oldName)
		newName = self.promptName("Rename", "New name:", oldName)
		if not newName or newName == oldName:
			return
		newPath = os.path.join(self.editor.explorerPath, newName)
		if os.path.exists(newPath) and newName.lower() != oldName.lower():
			self.say(f"'{newName}' already exists")
			return
		try:
			affected = buffersUnder(self.editor, oldPath)
			oldBase = os.path.abspath(oldPath)
			os.rename(oldPath, newPath)
			newBase = os.path.abspath(newPath)
			for buffer in affected:
				buffer.filename = newBase + os.path.abspath(buffer.filename)[len(oldBase):]
			self.rebuild(select=newName)
			self.say(f"Renamed to {newName}")
		except Exception as e:
			self.say(f"Rename failed: {e}")

	def deleteSelected(self):
		item = self.listWidget.currentItem()
		if not item:
			return
		name = item.data(Qt.ItemDataRole.UserRole)
		path = os.path.join(self.editor.explorerPath, name)

		from frontend.qt.app import QuiverDialog
		outcome = QuiverDialog.ask(
			"DELETE",
			f"Delete '{name}'? This can't be undone.",
			self.font,
			self.window()
		)
		if outcome != "yes":
			return
		row = self.listWidget.currentRow()
		try:
			affected = buffersUnder(self.editor, path)
			if os.path.isdir(path):
				shutil.rmtree(path)
			else:
				os.remove(path)
			for buffer in affected:
				for index, candidate in enumerate(self.editor.buffers):
					if candidate is buffer:
						removeBuffer(self.editor, index, remember=False)
						break
			self.rebuild(select=None)
			if self.listWidget.count() > 0:
				self.listWidget.setCurrentRow(min(row, self.listWidget.count() - 1))
			self.say(f"Deleted {name}")
		except Exception as e:
			self.rebuild()
			self.say(f"Delete failed: {e}")

	def showContextMenu(self, pos):
		item = self.listWidget.itemAt(pos)
		menu = QMenu(self)
		newFileAction = menu.addAction("New File (Ctrl+N)")
		newFolderAction = menu.addAction("New Folder (Ctrl+Shift+N)")
		renameAction = deleteAction = copyAction = None
		if item:
			self.listWidget.setCurrentItem(item)
			menu.addSeparator()
			renameAction = menu.addAction("Rename (F2)")
			deleteAction = menu.addAction("Delete (Del)")
			copyAction = menu.addAction("Copy Path")

		chosen = menu.exec(self.listWidget.viewport().mapToGlobal(pos))
		if chosen is None:
			return
		if chosen == newFileAction:
			self.createFile()
		elif chosen == newFolderAction:
			self.createFolder()
		elif chosen == renameAction:
			self.renameSelected()
		elif chosen == deleteAction:
			self.deleteSelected()
		elif chosen == copyAction:
			name = item.data(Qt.ItemDataRole.UserRole)
			QApplication.clipboard().setText(os.path.abspath(os.path.join(self.editor.explorerPath, name)))
