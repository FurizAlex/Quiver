import os
from commands.fileCommands import openFileBuffer
from PyQt6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QPushButton, QHBoxLayout
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

		if self.editor.showExplorer and getattr(self.editor, "explorerFocused", False):
			painter.fillRect(0, self.height() - 2, self.width(), 2, QColor(getColor("PALETTE_TITLE")))

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

		metrics = QFontMetrics(font)
		buttonH = metrics.height() + 4

		self.backButton = QPushButton("← ..")
		self.backButton.setFont(font)
		self.backButton.setFixedHeight(buttonH)
		self.backButton.clicked.connect(self.goBack)

		self.newFolderButton = QPushButton("+ DIR")
		self.newFolderButton.setFont(font)
		self.newFolderButton.setFixedHeight(QFontMetrics(font).height() + 4)
		self.newFolderButton.setFixedWidth(metrics.horizontalAdvance("+ DIR") + 20)
		self.newFolderButton.clicked.connect(self.createFolder)

		buttonRowWidget = QWidget()
		buttonRowWidget.setFixedHeight(buttonH)
		buttonRowLayout = QHBoxLayout(buttonRowWidget)
		buttonRowLayout.setContentsMargins(0, 0, 0, 0)
		buttonRowLayout.setSpacing(0)
		buttonRowLayout.addWidget(self.backButton, stretch=1)
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

		from PyQt6.QtCore import QTimer
		self.refreshTimer = QTimer()
		self.refreshTimer.setInterval(2000)
		self.refreshTimer.timeout.connect(self.autoRefresh)
		self.refreshTimer.start()

		editor.signals.changed.connect(self.syncVisibility)
		editor.signals.changed.connect(self.updateStyle)
		self.backButton.setFocusPolicy(Qt.FocusPolicy.TabFocus)
		self.newFolderButton.setFocusPolicy(Qt.FocusPolicy.TabFocus)
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
		self.newFolderButton.setStyleSheet(
            "QPushButton { background: " + selectBg + "; color: " + selectFg + "; "
            "border: none; padding-left: 6px; }"
            "QPushButton:hover { background: " + explorerFg + "; color: " + explorerBg + "; }"
        )

	def syncVisibility(self):
		self.setVisible(self.editor.showExplorer)

	def goBack(self):
		parent = os.path.dirname(os.path.abspath(self.editor.explorerPath))
		if parent != os.path.abspath(self.editor.explorerPath):
			self.editor.setExplorerPath(parent)
			self.rebuild()
			self.editor.notifyChanged()

	def autoRefresh(self):
		import os
		path = self.editor.explorerPath
		try:
			current = sorted(os.listdir(path))
			existing = [
				self.listWidget.item(i).data(Qt.ItemDataRole.UserRole)
				for i in range(self.listWidget.count())
			]
			if current != existing:
				self.rebuild()
		except Exception:
			pass

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
		if self.listWidget.count() > 0:
			self.listWidget.setCurrentRow(0)

	def openSelectedFile(self, item):
		name = item.data(Qt.ItemDataRole.UserRole)
		filepath = os.path.join(self.editor.explorerPath, name)
		if os.path.isdir(filepath):
			self.editor.setExplorerPath(filepath)
			self.rebuild()
		else:
			openFileBuffer(self.editor, filepath)
			self.editor.notifyChanged()

	def focusExplorer(self):
		self.listWidget.setFocus()
		if self.listWidget.count() > 0 and self.listWidget.currentRow() == -1:
			self.listWidget.setCurrentRow(0)

	def eventFilter(self, obj, event):
		from PyQt6.QtCore import QEvent
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
				if key == Qt.Key.Key_Escape or key == Qt.Key.Key_Tab:
					self.returnToEditor()
					return True
				if key == Qt.Key.Key_Backspace:
					self.goBack()
					return True
				if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
					item = self.listWidget.currentItem()
					if item:
						self.openSelectedFile(item)
					return True
				if key == Qt.Key.Key_N and mods & Qt.KeyboardModifier.ControlModifier:
					mods = event.modifiers()
					if mods & Qt.KeyboardModifier.ControlModifier:
						self.createFolder()
						return True
				if key == Qt.Key.Key_F and mods & Qt.KeyboardModifier.ControlModifier:
					mods = event.modifiers()
					if mods & Qt.KeyboardModifier.ControlModifier:
						self.createFolder()
						return True
				if key == Qt.Key.Key_F2:
					self.renameSelected()
					return True
				if key == Qt.Key.Key_Delete:
					self.deleteSelected()
					return True
		return False
	
	def renameSelected(self):
		item = self.listWidget.currentItem()
		if not item:
			return
		oldName = item.data(Qt.ItemDataRole.UserRole)
		oldPath = os.path.join(self.editor.explorerPath, oldName)

		from PyQt6.QtWidgets import QInputDialog
		newName, ok = QInputDialog.getText(self, "Rename", "New name: ", text=oldName)
		if not ok or not newName.strip() or newName.strip() == oldName:
			return
		newPath = os.path.join(self.editor.explorerPath, newName.strip())
		try:
			os.rename(oldPath, newPath)
			for buffer in self.editor.buffers:
				if buffer.filename and os.path.abspath(buffer.filename) == os.path.abspath(oldPath):
					buffer.filename = newPath
			self.rebuild()
			self.editor.status = f"Renamed to {newName.strip()}"
			self.editor.statusTimer = 120
			self.editor.notifyChanged()
		except Exception as e:
			self.editor.status = f"Rename failed: {e}"
			self.editor.statusTimer = 120
			self.editor.notifyChanged()

	def deleteSelected(self):
		item = self.listWidget.currentItem()
		if not item:
			return
		name = item.data(Qt.ItemDataRole.UserRole)
		path = os.path.join(self.editor.explorerPath, name)

		from frontend.qt.app import QuiverDialog
		outcome = QuiverDialog.ask(
			"DELETE",
			f"Delete '{name}? This can't be undone.",
			self.font,
			self 
		)
		if outcome != "yes":
			return
		try:
			if os.path.isdir(path):
				import shutil
				shutil.rmtree(path)
			else:
				os.remove(path)
			absPath = os.path.abspath(path)
			for buffer in list(self.editor.buffers):
				if buffer.filename and os.path.abspath(buffer.filename) == absPath:
					index = self.editor.buffers.index(buffer)
					self.editor.buffers.removee(buffer)
					self.editor.currentBuffer = min(self.editor.currentBuffer, len(self.editor.buffers) - 1)
					replacement = self.editor.buffers[self.editor.currentBuffer]
					for pane in self.editor.panes:
						if pane.buffer is buffer:
							pane.buffer = replacement
			self.rebuild()
			self.editor.status = f"Deleted {name}"
			self.editor.statusTimer = 120
			self.editor.notifyChanged()
		except Exception as e:
			self.editor.status = f"Deleted FAILED: {e}"
			self.editor.statusTimer = 120
			self.editor.notifyChanged()

	def showContextMenu(self, pos):
		item = self.listWidget.itemAt(pos)
		if not item:
			return
		self.listWidget.setCurrentItem(item)

		from PyQt6.QtWidgets import QMenu
		menu = QMenu(self)
		renameAction = menu.addAction("Rename (F2)")
		deleteAction = menu.addAction("Delete (Del)")

		chosen = menu.exec(self.listWidget.mapToGlobal(pos))
		if chosen == renameAction:
			self.renameSelected()
		elif chosen == deleteAction:
			self.deleteSelected()

	def returnToEditor(self):
		w = self.parent()
		while w is not None:
			if hasattr(w, "views"):
				panes = w.views.paneContainer.paneViews
				if panes:
					panes[w.editor.activePane].setFocus()
				return
			w = w.parent()
		from PyQt6.QtWidgets import QApplication
		for widget in QApplication.topLevelWidgets():
			if hasattr(widget, "views"):
				panes = widget.views.paneContainer.paneViews
				if panes:
					panes[widget.editor.activePane].setFocus()
				return

	def createFolder(self):
		from PyQt6.QtWidgets import QInputDialog
		name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
		if ok and name.strip():
			import os
			newPath = os.path.join(self.editor.explorerPath, name.strip())
			try:
				os.makedirs(newPath, exist_ok=True)
				self.rebuild()
				self.editor.notifyChanged()
			except Exception as e:
				pass