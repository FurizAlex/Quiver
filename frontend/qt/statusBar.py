from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt

class StatusBar(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.leftLabel = QLabel()
		self.rightLabel = QLabel()
		self.leftLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
		self.rightLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
		
		layout = QHBoxLayout()
		layout.setContentsMargins(6, 0, 6, 0)
		layout.setSpacing(0)

		layout.addWidget(self.leftLabel)
		layout.addStretch()
		layout.addWidget(self.rightLabel)

		self.setLayout(layout)
		self.setFixedHeight(24)
		self.setObjectName("statusBar")

	def updateState(self, editor):
		buffer = editor.pane.buffer
		filename = buffer.filename or "[NO FILE]"
		diagosticCount = buffer.diagnostics.count() if hasattr(buffer, "diagnostics") else 0
		status = editor.status
		if status.startswith("KEY="):
			status = ""
		if editor.saving:
			left = f"SAVE AS: {editor.saveInput}_"
		else:
			languageName = buffer.language.name.upper() if buffer.language else "TEXT"
			left = (
				f"{editor.mode} | "
				f"{filename} | "
				f"Diag {diagosticCount} | "
				f"Ln {editor.pane.cursorY + 1} | "
				f"Col {editor.pane.cursorX + 1} | "
				f"{languageName} | "
			)
			if status:
				left += f"  |  {status}"
		right = (
			"^S Save  "
			"^O Open  "
			"^P Commands  "
			"^N Next"
		)
		self.leftLabel.setText(left)
		self.rightLabel.setText(right)