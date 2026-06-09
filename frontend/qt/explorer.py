import os
from commands.fileCommands import openFileBuffer
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

class Explorer(QListWidget):
	def __init__(self, editor):
		super().__init__()
		self.editor = editor
		self.setObjectName("explorer")
		self.setFixedWidth(220)
		self.itemDoubleClicked.connect(self.openSelectedFile)

	def rebuild(self):
		self.clear()
		path = self.editor.explorerPath
		try:
			for name in sorted(os.listdir(path)):
				fullPath = os.path.join(path, name)
				if os.path.isdir(fullPath):
					label = f"> {name}"
				else:
					label = f"- {name}"
				item = QListWidgetItem(label)
				item.setData(Qt.ItemDataRole.UserRole, name)
				self.addItem(item)
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