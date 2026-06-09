#app.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PyQt6.QtCore import Qt

from frontend.qt.qtTheme import loadQtTheme
from frontend.qt.editorQt import EditorQt, EditorSignals

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter
from frontend.qt.statusBar import StatusBar
from frontend.qt.editorView import EditorView
from frontend.qt.tabBar import TabBar
from frontend.qt.titleBar import TitleBar
from frontend.qt.explorer import Explorer

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.editor = EditorQt()

		central = QWidget()
		layout = QVBoxLayout(central)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		self.tabs = TabBar(self.editor)
		self.tabs.rebuild()
		
		self.titleBar = TitleBar(self.editor)

		self.explorer = Explorer(self.editor)
		self.explorer.rebuild()

		self.views = EditorView(self.editor)

		splitter = QSplitter(Qt.Orientation.Horizontal)
		splitter.setHandleWidth(1)
		splitter.addWidget(self.explorer)
		splitter.addWidget(self.views)
		splitter.setStretchFactor(1, 1)
		splitter.setSizes([220, 9999])

		self.statusBarWidget = StatusBar()

		for sig in (
			self.editor.signals.cursorMoved,
			self.editor.signals.changed,
			self.editor.signals.statusChanged
		):
			sig.connect(lambda *_: self.statusBarWidget.updateState(self.editor))
		
		layout.addWidget(self.tabs)
		layout.addWidget(self.titleBar)
		layout.addWidget(splitter, stretch=1)
		layout.addWidget(self.statusBarWidget)

		self.setCentralWidget(central)
		self.setWindowTitle("Quiver")
		self.resize(1280, 720)
		self.setMinimumSize(1000, 700)

		self.statusBarWidget.updateState(self.editor)
		self.views.setFocus()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setStyleSheet(loadQtTheme("quiver"))
	window = MainWindow()
	window.show()
	window.editor.resize(window.width(), window.height())
	sys.exit(app.exec())