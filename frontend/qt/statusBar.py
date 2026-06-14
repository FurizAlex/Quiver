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
		foreground = getColor("STATUS_FG")
		filename = buffer.filename or "[NO FILE]"
		diagosticCount = buffer.diagnostics.count() if hasattr(buffer, "diagnostics") else 0
		status = editor.status or ""
		for label in (self.leftLabel, self.rightLabel):
			label.setStyleSheet(f"background: transparent; color: {foreground};")
		select = editor.selection
		selectInfo = ""
		if select.active:
			n = select.normalized()
			if n["sy"] == n["ey"]:
				chars = n["ex"] - n["sx"]
				selectInfo = f"  |  SEL {chars}ch"
			else:
				lines = n["ey"] - n["sy"] + 1
				selectInfo = f"  |  SEL {lines}ln"
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
				f"{languageName}"
				f"{selectInfo}"
			)
			if status:
				left += f"  |  {status}"
		if not hasattr(editor, "signals"):
			if editor.focus == "explorer":
				right = "↑↓ Navigate  ENTER Open  BKSP Back  TAB Editor"
			else:
				right = "^S Save  ^O Open  ^P Commands  ^N Next"
		else:
			right = "^S Save  ^O Open  ^P Commands  ^N Next  ^E Explorer"
		self.leftLabel.setText(left)
		self.rightLabel.setText(right)