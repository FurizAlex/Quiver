from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt

class TitleBar(QWidget):
	def __init__(self, editor):
		super().__init__()
		self.editor = editor
		self.setObjectName("titleBar")
		self.setFixedHeight(24)

		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)

		self.label = QLabel()
		self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.label.setObjectName("titleBarLabel")
		layout.addWidget(self.label)

		editor.signals.changed.connect(self.refresh)
		self.refresh()

	def refresh(self):
		buffer = self.editor.pane.buffer
		name = buffer.name.upper()
		if buffer.modified:
			name += " *"
		self.label.setText(name)