from PyQt6.QtWidgets import QTabBar

class TabBar(QTabBar):
	def __init__(self, editor):
		super().__init__()
		self.editor = editor
		self.setObjectName("tabBar")
		self.rebuildings = False
		self.currentChanged.connect(self.tabChanged)

		editor.signals.changed.connect(self.rebuild)
		editor.signals.panesChanged.connect(self.rebuild)

	def rebuild(self):
		self.rebuildings = True
		active = self.editor.currentBuffer
		while self.count():
			self.removeTab(0)
		
		for buffer in self.editor.buffers:
			name = buffer.name.upper()
			if buffer.modified:
				name += " *"
			self.addTab(name)
		if 0 <= active < self.count():
			self.setCurrentIndex(active)
		self.rebuildings = False

	def tabChanged(self, index):
		if self.rebuildings:
			return
		if index < 0 or index >= len(self.editor.buffers):
			return
		self.editor.currentBuffer = index
		self.editor.pane.buffer = self.editor.buffers[index]
		self.editor.notifyChanged()