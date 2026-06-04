from PyQt6.QtWidgets import QWidget, QLabel, QSplitter
from PyQt6.QtCore import Qt

class StatusBar(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.leftLabel = QLabel()
		self.rightLabel = QLabel()
		self.leftLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
		self.rightLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
		
		layout = QSplitter()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setHandleWidth(1)

		layout.addWidget(self.leftLabel)
		layout.addStretch()
		layout.addWidget(self.rightLabel)

		self.setLayout(layout)
		self.setFixedHeight(24)
		self.setObjectName("statusBar")

	def updateState(self, editor):
		filename = editor.filename or "UNTITLED"
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
				f"{editor.pane.buffer.language.name.upper() if editor.pane.buffer.language else "TEXT"}"
			)
		right = (
			"^S Save  "
			"^O Open  "
			"^P Commands  "
			"^N Next"
		)
		self.leftLabel.setText(left)
		self.rightLabel.setText(right)