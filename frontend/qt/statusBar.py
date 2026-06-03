from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout

class StatusBar(QWidget):
	def __init__(self):
		super().__init__()
		layout = QHBoxLayout(self)
		
		self.position = QLabel("Ln 1, Col 1")
		self.encoding = QLabel("UTF-8")
		self.lineEnding = QLabel("LF")
		self.language = QLabel("Plain Text")

		layout.addWidget(self.position)
		layout.addStretch()
		layout.addWidget(self.encoding)
		layout.addWidget(self.lineEnding)
		layout.addWidget(self.language)

	def setPosition(self, line, column):
		self.position.setText(f"Ln {line}, Col {column}")