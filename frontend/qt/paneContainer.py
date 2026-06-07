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
		self.layout = QHBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)

		self.paneViews = []

		self.splitter = QSplitter(Qt.Orientation.Horizontal)

		self.layout.addWidget(self.splitter)
		self.setLayout(self.layout)

		editor.signals.panesChanged.connect(self.rebuildPanes)
		self.rebuildPanes()

	def rebuildPanes(self):
		while self.splitter.count():
			widget = self.splitter.widget(0)
			self.splitter.removeWidget(widget)
			widget.deleteLater()

		from frontend.qt.editorView import PaneView
		for pane in self.editor.panes:
			view = PaneView(self.editor, pane, self.font)
			self.splitter.addWidget(view)

	def rebuildPanes(self):
		while self.splitter.count():
			widget = self.splitter.widget(0)

			self.splitter.removeWidget(widget)
			widget.deleteLater()
		self.paneViews.clear()

		from frontend.qt.editorView import PaneView
		for pane in self.editor.panes:
			view = PaneView(self.editor, pane, self.font)
			self.splitter.addWidget(view)
			self.paneViews.append(view)

	def focusNextPane(self):
		if not self.panes:
			return
		current = self.activePane
		index = self.panes.index(current)
		nextIndex = (index + 1) % len(self.panes)

		self.setActivePane(self.panes[nextIndex])
