from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter
from frontend.qt.amigaPalette import getColor

STATUS_LIFETIME_MS = 4000

class StatusBar(QWidget):
	def __init__(self, font: QFont, parent=None):
		super().__init__(parent)
		metrics = font.pointSize()
		self.setObjectName("statusBar")
		self.setFixedHeight(metrics * 3)

		self.leftLabel = QLabel()
		self.rightLabel = QLabel()
		self.lastForeground = None
		self.lastStatus = ""
		self.editorRef = None

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

		# status messages used to stay on screen forever - expire them
		self.statusExpiry = QTimer(self)
		self.statusExpiry.setSingleShot(True)
		self.statusExpiry.timeout.connect(self.expireStatus)

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.fillRect(self.rect(), QColor(getColor("STATUS_BG")))
		painter.setPen(QColor(getColor("STATUS_FG")))
		painter.drawLine(0, 0, self.width(), 0)

	def expireStatus(self):
		editor = self.editorRef
		if editor is None or getattr(editor, "splitterResizeMode", False):
			return
		if (editor.status or "") == self.lastStatus:
			editor.status = ""
			editor.notifyChanged()

	def trackStatus(self, editor, status):
		if status == self.lastStatus:
			return
		self.lastStatus = status
		if status and not getattr(editor, "splitterResizeMode", False):
			self.statusExpiry.start(STATUS_LIFETIME_MS)
		else:
			self.statusExpiry.stop()

	def updateState(self, editor):
		self.editorRef = editor
		pane = editor.pane
		buffer = pane.buffer
		foreground = getColor("STATUS_FG")
		if foreground != self.lastForeground:
			self.lastForeground = foreground
			for label in (self.leftLabel, self.rightLabel):
				label.setStyleSheet(f"background: transparent; color: {foreground};")

		filename = buffer.filename or "[NO FILE]"
		if buffer.modified:
			filename += " *"
		diagnosticCount = buffer.diagnostics.count() if hasattr(buffer, "diagnostics") else 0
		status = editor.status or ""
		if status.startswith("KEY=") or status.startswith("'"):
			status = ""
		self.trackStatus(editor, editor.status or "")

		select = editor.selection
		selectInfo = ""
		if select.active:
			n = select.normalized()
			if n["sy"] == n["ey"]:
				selectInfo = f"  |  SEL {n['ex'] - n['sx']}ch"
			else:
				selectInfo = f"  |  SEL {n['ey'] - n['sy'] + 1}ln"

		cursorCount = len(pane.multiCursor.cursors) if pane.multiCursor.isMulti() else 1
		cursorInfo = f"  |  {cursorCount} CURSORS" if cursorCount > 1 else ""

		settings = editor.settings
		indentInfo = f"TAB {settings.tabSize}" if settings.useTabs else f"SPACES {settings.tabSize}"

		if editor.saving:
			left = f"SAVE AS: {editor.saveInput}_"
		else:
			languageName = buffer.language.name.upper() if buffer.language else "TEXT"
			left = (
				f"{editor.mode} | "
				f"{filename} | "
				f"Diag {diagnosticCount} | "
				f"Ln {pane.cursorY + 1}/{len(buffer.lines)} | "
				f"Col {pane.cursorX + 1} | "
				f"{indentInfo} | "
				f"{languageName}"
				f"{selectInfo}"
				f"{cursorInfo}"
			)
			if status:
				left += f"  |  {status}"

		if getattr(editor, "explorerFocused", False):
			right = "ENTER Open  BKSP Up  ^N New  F2 Rename  DEL Delete  TAB Editor"
		else:
			right = "^S Save  ^O Open  ^P Commands  ^N Next  ^E Explorer"
		self.leftLabel.setText(left)
		self.rightLabel.setText(right)
