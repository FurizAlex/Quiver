import os
from commands.fileCommands import openFileBuffer
from PyQt6.QtWidgets import QListWidget

class Explorer(QListWidget):
	def __init__(self, editor):
		super().__init__()
		self.editor = editor
		self.currentRowChanged.connect(self.openFile)

	def rebuild(self):
		self.clear()
		for item in sorted(os.listdir(".")):
			self.addItem(item)

	def openFile(self, index):
		item = self.item(index)
		if item:
			openFileBuffer(self.editor, item.text())