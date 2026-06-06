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
		filename = editor.filename or "[NO FILE]"
		diagosticCount = editor.pane.buffer.diagnostics.count() if hasattr(editor.pane.buffer, "diagnostics") else 0
		if editor.saving:
			left = f"SAVE AS: {editor.saveInput}"
		else:
			left = (
				f"{editor.mode} | "
				f"{filename} | "
				f"Diag {diagosticCount} | "
				f"Ln {editor.pane.cursorY + 1} | "
				f"Col {editor.pane.cursorX + 1} | "
				f"{editor.pane.buffer.language.name.upper() if editor.pane.buffer.language else "TEXT"} | "
				f"{editor.status} |"
			)
		right = (
			"^S Save  "
			"^O Open  "
			"^P Commands  "
			"^N Next"
		)
		self.leftLabel.setText(left)
		self.rightLabel.setText(right)