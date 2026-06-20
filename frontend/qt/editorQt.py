import sys
from PyQt6.QtCore import QObject
from PyQt6.QtCore import pyqtSignal

from core.editor import Editor

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

class EditorSignals(QObject):
	changed = pyqtSignal()
	cursorMoved = pyqtSignal()
	statusChanged = pyqtSignal()
	panesChanged = pyqtSignal()
	def __init__(self):
		super().__init__()

class EditorQt(Editor):
	def __init__(self):
		super().__init__(None)
		self.signals = EditorSignals()

	def notifyChanged(self):
		self.signals.changed.emit()

	def notifyCursorMoved(self):
		self.signals.cursorMoved.emit()

	def notifyStatusChanged(self):
		self.signals.statusChanged.emit()

	def notifyPanesChanged(self):
		self.signals.panesChanged.emit()

	def handleInput(self, event):
		super().handleInput(event)

	@property
	def pane(self):
		return self.panes[self.activePane]