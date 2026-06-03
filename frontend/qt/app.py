import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.editor import Editor
from frontend.qt.editorQt import EditorSignals

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter
from frontend.qt.statusBar import StatusBar
from frontend.qt.editorView import EditorView
from frontend.qt.tabBar import TabBar
from frontend.qt.explorer import Explorer

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.editor = Editor(None)
		self.signals = EditorSignals()
		central = QWidget()
		layout = QVBoxLayout()

		self.explorer = Explorer(self.editor)
		self.tabs = TabBar(self.editor)
		self.views = EditorView(self.editor)
		self.statusBarWidget = StatusBar()

		splitter = QSplitter()
		splitter.addWidget(self.explorer)
		splitter.addWidget(self.views)
		splitter.setStretchFactor(1, 1)

		layout.addWidget(self.tabs)
		layout.addWidget(splitter)
		layout.addWidget(self.statusBarWidget)

		central.setLayout(layout)
		self.setCentralWidget(central)

		self.setWindowTitle("Quiver")
		self.resize(1280, 720)
		self.setMinimumSize(1000, 700)

		self.views.cursorChanged.connect(self.statusBarWidget.setPosition)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	window.editor.resize(window.width(), window.height())
	sys.exit(app.exec())