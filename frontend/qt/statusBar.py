from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter
from frontend.qt.amigaPalette import getColor

class StatusBar(QWidget):
	def __init__(self, font: QFont, parent=None):
		super().__init__(parent)
		metrics = font.pointSize()
		self.setObjectName("statusBar")
		self.setFixedHeight(metrics * 3)

		self.leftLabel = QLabel()
		self.rightLabel = QLabel()

		for label in (self.leftLabel, self.rightLabel):
			label.setFont(font)
			label.setStyleSheet("background: transparent; color: white;")
		self.leftLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
		self.rightLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
		
		layout = QHBoxLayout(self)
		layout.setContentsMargins(6, 0, 6, 0)
		layout.setSpacing(0)

		layout.addWidget(self.leftLabel)
		layout.addStretch()
		layout.addWidget(self.rightLabel)

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.fillRect(self.rect(), QColor(getColor("STATUS_BG")))
		painter.setPen(QColor(getColor("STATUS_FG")))
		painter.drawLine(0, 0, self.width(), 0)

	def updateState(self, editor):
		buffer = editor.pane.buffer
		filename = buffer.filename or "[NO FILE]"
		diagosticCount = buffer.diagnostics.count() if hasattr(buffer, "diagnostics") else 0
		status = editor.status or ""
		fg = getColor("STATUS_FG")
		for label in (self.leftLabel, self.rightLabel):
			label.setStyleSheet(f"background: transparent; color: {fg};")
		if status.startswith("KEY=") or status.startswith("'"):
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