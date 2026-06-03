from PyQt6.QtWidgets import QTabBar

class TabBar(QTabBar):
	def __init__(self, editor):
		super().__init__()
		self.editor = editor
		self.currentChanged.connect(self.changeTab)

	def rebuild(self):
		while self.count():
			self.removeTab(0)
		
		for buffer in self.editor.buffers:
			self.addTab(buffer.name)

	def changeTab(self, index):
		if index < 0:
			return
		self.editor.currentBuffer = index
		self.editor.pane.buffer = self.editor.buffers[index]