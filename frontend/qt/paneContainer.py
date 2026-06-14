import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt

class PaneContainer(QWidget):
	def __init__(self, editor, font):
		super().__init__()
		self.editor = editor
		self.font = font
		self.paneViews = []

		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		self.splitter = QSplitter(Qt.Orientation.Horizontal)
		self.splitter.setHandleWidth(0)
		layout.addWidget(self.splitter)

		editor.signals.panesChanged.connect(self.rebuildPanes)
		self.rebuildPanes()

	def rebuildPanes(self):
		for view in self.paneViews:
			view.setParent(None)
			view.deleteLater()
		self.paneViews.clear()

		from frontend.qt.editorView import PaneView
		for i, pane in enumerate(self.editor.panes):
			view = PaneView(self.editor, pane, self.font, paneIndex=i)
			self.splitter.addWidget(view)
			self.paneViews.append(view)

		index = self.editor.activePane
		if 0 <= index < len(self.paneViews):
			self.paneViews[index].setFocus()

	def focusNextPane(self):
		if not self.paneViews:
			return
		index = (self.editor.activePane + 1) % len(self.paneViews)
		self.editor.activePane = index
		self.paneViews[index].setFocus()
		self.editor.notifyChanged()
