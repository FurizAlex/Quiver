from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget

class CommandPalette(QDialog):
	def __init__(self, editor):
		super().__init__()
		self.editor = editor

		layout = QVBoxLayout()

		self.search = QLineEdit()
		self.results = QListWidget()

		layout.addWidget(self.search)
		layout.addWidget(self.results)

		self.setLayout(layout)
		
		self.search.textChanged.connect(self.filterCommands)

	def filterCommands(self, text):
		self.results.clear()

		for command in self.editor.commands:
			if text.lower() in command.name.lower():
				self.results.addItem(command.name)