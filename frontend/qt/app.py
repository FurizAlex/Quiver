#app.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PyQt6.QtCore import Qt

from frontend.qt.qtTheme import loadQtTheme
from frontend.qt.editorQt import EditorQt

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter, QSplitterHandle
from PyQt6.QtGui import QFontDatabase, QFont, QPainter, QColor, QPen
from frontend.qt.statusBar import StatusBar
from frontend.qt.editorView import EditorView
from frontend.qt.explorer import Explorer
from frontend.qt.tabBar import TabBar

def loadAppFont():
	fontID = QFontDatabase.addApplicationFont("assets/fonts/Terminus.ttf")
	if fontID != -1:
		family = QFontDatabase.applicationFontFamilies(fontID)[0]
	else:
		family = "Courier New"
	font = QFont(family)
	font.setPointSize(16)
	font.setBold(True)
	font.setStyleHint(QFont.StyleHint.TypeWriter)
	font.setStyleStrategy(QFont.StyleStrategy.NoFontMerging | QFont.StyleStrategy.PreferBitmap)
	return font

class DashedSpliiter(QSplitter):
	def createHandle(self):
		return DashedHandle(self.orientation(), self)
	
class DashedHandle(QSplitterHandle):
	def paintEvent(self, event):
		painter = QPainter(self)
		painter.fillRect(self.rect(), QColor("#000000"))
		from PyQt6.QtGui import QPen
		pen = QPen(QColor("#FFFFFF"))
		pen.setStyle(Qt.PenStyle.DashLine)
		pen.setWidth(1)
		painter.setPen(pen)
		cx = self.width() // 2
		painter.drawLine(cx, 0, cx, self.height())

class BorderOverlay(QWidget):
	MARGIN = 12
	def __init__(self, parent):
		super().__init__(parent)
		self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

	def paintEvent(self, event):
		margin = self.MARGIN
		painter = QPainter(self)
		pen = QPen(QColor("#FFFFFF"))
		pen.setWidth(1)
		painter.setPen(pen)
		painter.drawRect(margin, margin, self.width() - margin * 2 - 1, self.height() - margin * 2 - 1)

class MainWindow(QMainWindow):
	CONTENT_MARGIN = BorderOverlay.MARGIN + 2
	def __init__(self, appFont: QFont):
		super().__init__()
		self.editor = EditorQt()
		self.editor.qtWindow = self
		self.appFont = appFont

		margin = self.CONTENT_MARGIN

		root = QWidget()
		root.setStyleSheet("background: black;")
		rootLayout = QVBoxLayout(root)
		rootLayout.setContentsMargins(margin, margin, margin, margin)
		rootLayout.setSpacing(0)

		self.explorer = Explorer(self.editor, appFont)
		self.explorer.rebuild()

		self.tabBar = TabBar(self.editor, appFont)
		self.views = EditorView(self.editor, appFont)

		splitter = DashedSpliiter(Qt.Orientation.Horizontal)
		splitter.setHandleWidth(8)
		splitter.addWidget(self.explorer)
		splitter.addWidget(self.views)
		splitter.setStretchFactor(1, 1)
		splitter.setSizes([200, 9999])

		self.statusBarWidget = StatusBar(appFont)
		self.statusBarWidget.setStyleSheet("background: #0000AA; color: white; border-top: 1px solid white;")
		for sig in (
			self.editor.signals.cursorMoved,
			self.editor.signals.changed,
			self.editor.signals.statusChanged
		):
			sig.connect(lambda *_: self.statusBarWidget.updateState(self.editor))
		
		rootLayout.addWidget(self.tabBar)
		rootLayout.addWidget(splitter, stretch=1)
		rootLayout.addWidget(self.statusBarWidget)
		self.setCentralWidget(root)

		self.border = BorderOverlay(root)
		self.border.raise_()

		self.setWindowTitle("Quiver")
		self.resize(1280, 720)
		self.setMinimumSize(800, 550)

		self.statusBarWidget.updateState(self.editor)
		self.views.setFocus()

	def applyQtTheme(self, themeDef: dict):
		from frontend.qt.amigaPalette import getColor
		explorerBg			= getColor("EXPLORER_BG")
		explorerFg			= getColor("EXPLORER_FG")
		explorerSelectBg	= getColor("EXPLORER_SELECT_BG")
		explorerSelectFg	= getColor("EXPLORER_SELECT_FG")

		listQss = (
			"QListWidget { background: " + explorerBg + "; color: " + explorerFg + "; "
			"border: none; outline: none; }"
			"QListWidget::item { background: " + explorerBg + "; color: " + explorerFg + "; "
			"padding: 1px 4px; }"
			"QListWidget::item:selected { background: " + explorerSelectBg + "; "
			"color: " + explorerSelectFg + "; }"
			"QListWidget::item:hover { background: " + explorerSelectBg + "; "
			"color: " + explorerSelectFg + "; }"
		)
		self.explorer.listWidget.setStyleSheet(listQss)
		self.explorer.listWidget.viewport().setStyleSheet("background: " + explorerBg + ";")
		self.explorer.header.update()
		self.statusBarWidget.update()
		self.editor.notifyChanged()

	def closeEvent(self, event):
		unsaved = [b.name for b in self.editor.buffers if b.modified]
		if unsaved:
			from PyQt6.QtWidgets import QMessageBox
			names = ", ".join(unsaved)
			reply = QMessageBox.question(
				self,
				"Unsaved Changes",
				f"Wait! You haven't saved on\n{names}\n\nWould you still like to quit?",
				QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
				QMessageBox.StandardButton.No
			)
			if reply != QMessageBox.StandardButton.Yes:
				event.ignore()
				return
		event.accept()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		if hasattr(self, "_border"):
			self.border.resize(self.centralWidget().size())
			self.border.raise_()

	def showEvent(self, event):
		super().showEvent(event)
		self.border.resize(self.centralWidget().size())
		self.border.raise_()
		self.views.paneContainer.paneViews[0].setFocus()

	def newFileQt(self):
		if self.pane.buffer.modified:
			from PyQt6.QtWidgets import QMessageBox
			reply = QMessageBox.question(
			None, "UNSAVED CHANGES", f"'{self.pane.buffer.name}' has unsaved changes. Would you like to create a new file anyway?",
			QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
			QMessageBox.StandardButton.No
		)
		if reply != QMessageBox.StandardButton.Yes:
			return
		from core.buffer import Buffer
		buffer = Buffer(editor=self, language=self.languageRegistry.get("text"))
		self.buffers.append(buffer)
		self.currentBuffer = len(self.buffers) - 1
		self.pane.buffer = buffer
		self.pane.cursorX = 0
		self.pane.cursorY = 0
		self.notifyChanged()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	appFont = loadAppFont()
	app.setFont(appFont)
	app.setStyleSheet(loadQtTheme("quiver"))
	window = MainWindow(appFont)
	savedTheme = window.editor.settings.get("theme", "quiver")
	try:
		import importlib
		themeModule = importlib.import_module(f"themes.{savedTheme}")
		from frontend.qt.amigaPalette import applyThemeToQt
		applyThemeToQt(themeModule.THEME)
		window.applyQtTheme(themeModule.THEME)
	except Exception:
		pass
	window.show()
	window.editor.resize(window.width(), window.height())
	sys.exit(app.exec())