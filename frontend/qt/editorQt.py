import sys
from PyQt6.QtCore import QObject
from PyQt6.QtCore import pyqtSignal

from core.editor import Editor

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

class EditorQt(Editor):
	def __init__(self):
		super().__init__(None)
		self.signals = EditorSignals()

class EditorSignals(QObject):
	changed = pyqtSignal()
	def __init__(self):
		super().__init__()