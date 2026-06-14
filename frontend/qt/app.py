#app.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PyQt6.QtCore import Qt

from frontend.qt.qtTheme import loadQtTheme
from frontend.qt.editorQt import EditorQt

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter, QSplitterHandle, QHBoxLayout, QPushButton, QLabel, QDialog
from PyQt6.QtGui import QFontDatabase, QFont, QFontMetrics, QPainter, QColor, QPen, QIcon
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

class TitleBar(QWidget):
	def __init__(self, title: str, font: QFont, parent=None):
		super().__init__(parent)
		self.setFixedHeight(QFontMetrics(font).height() + 10)

		layout = QHBoxLayout(self)
		layout.setContentsMargins(8, 0, 4, 0)
		layout.setSpacing(0)

		self.titleLabel = QLabel(title)
		self.titleLabel.setFont(font)
		self.titleLabel.setStyleSheet("color: white; background: transparent;")

		self.buttonMin		= self.makeButton("#CCCC00", self.minimize)
		self.buttonMax		= self.makeButton("#00CC00", self.maximize)
		self.buttonClose	= self.makeButton("#CC0000", self.close)

		layout.addWidget(self.titleLabel)
		layout.addStretch()
		layout.addWidget(self.buttonMin)
		layout.addSpacing(4)
		layout.addWidget(self.buttonMax)
		layout.addSpacing(4)
		layout.addWidget(self.buttonClose)
		layout.addSpacing(4)

	def makeButton(self, color: str, slot) -> QPushButton:
		button = QPushButton()
		button.setFixedSize(14, 14)
		button.setStyleSheet(
			f"QPushButton {{ background: {color}; border: 1px solid white; }}"
			f"QPushButton:hover {{ background: white; }}"
		)
		button.clicked.connect(slot)
		return button
	
	def minimize(self):
		self.window().showMinimized()

	def maximize(self):
		w = self.window()
		if w.isMaximized():
			w.showNormal()
		else:
			w.showMaximized()

	def close(self):
		self.window().close()

	def paintEvent(self, event):
		painter = QPainter(self)
		from frontend.qt.amigaPalette import getColor
		painter.fillRect(self.rect(), QColor(getColor("STATUS_BG")))
		painter.setPen(QColor("#FFFFFF"))
		painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

	def mouseDoubleClickEvent(self, event):
		self.maximize()

class QuiverDialog(QDialog):
	def __init__(self, title: str, message: str, font: QFont, parent=None):
		super().__init__(parent, Qt.WindowType.FramelessWindowHint)
		self.setModal(True)
		self.setStyleSheet("background: black;")

		from frontend.qt.amigaPalette import getColor
		paletteBg	= getColor("PALETTE_BG")
		paletteFg	= getColor("PALETTE_FG")
		titleFg		= getColor("PALETTE_TITLE")

		outer = QVBoxLayout(self)
		outer.setContentsMargins(2, 2, 2, 2)
		outer.setSpacing(0)

		box = QWidget()
		box.setStyleSheet(f"background: {paletteBg}; border: 1px solid {paletteFg};")
		boxLayout = QVBoxLayout(box)
		boxLayout.setContentsMargins(16, 12, 16, 12)
		boxLayout.setSpacing(8)

		titleLabel = QLabel(title)
		titleLabel.setFont(font)
		titleLabel.setStyleSheet(f"color: {titleFg}; background: transparent; border: none;")

		msgLabel = QLabel(message)
		msgLabel.setFont(font)
		msgLabel.setStyleSheet(f"color: {paletteFg}; background: transparent; border: none;")
		msgLabel.setWordWrap(True)

		buttonRow = QHBoxLayout()
		buttonRow.setSpacing(8)

		self.buttonYes = QPushButton("YES")
		self.buttonNo = QPushButton("No")
		for button in (self.buttonYes, self.buttonNo):
			button.setFont(font)
			button.setFixedHeight(font.pointSize() * 3)
			button.setMinimumWidth(80)

		self.buttonYes.setStyleSheet(
			f"QPushButton {{ background: {paletteFg}; color: {paletteBg}; border: none; }}"
			f"QPushButton:hover {{ background: {titleFg}; color: {paletteBg}; }}"
		)
		self.buttonNo.setStyleSheet(
			f"QPushButton {{ background: transparent; color: {paletteFg}; "
			f"border: 1px solid {paletteFg}; }}"
			f"QPushButton:hover {{ background: {paletteFg}; color: {paletteBg}; }}"
		)
		self.buttonYes.clicked.connect(self.yes)
		self.buttonNo.clicked.connect(self.no)

		buttonRow.addStretch()
		buttonRow.addWidget(self.buttonNo)
		buttonRow.addWidget(self.buttonYes)

		boxLayout.addWidget(titleLabel)
		boxLayout.addWidget(msgLabel)
		boxLayout.addSpacing(4)
		boxLayout.addLayout(buttonRow)
		outer.addWidget(box)

		self.setFixedWidth(400)
		self.adjustSize()
	
	def yes(self):
		self.result = True
		self.close()

	def no(self):
		self.result = False
		self.close()

	@staticmethod
	def ask(title: str, message: str, font: QFont, parent=None):
		dialog = QuiverDialog(title, message, font, parent)
		if parent:
			geo = parent.geometry()
			dialog.move(
				geo.x() + (geo.width() - dialog.width()) // 2,
				geo.y() + (geo.height() - dialog.height()) // 2
			)
		dialog.exec()
		return dialog.result

class MainWindow(QMainWindow):
	CONTENT_MARGIN = BorderOverlay.MARGIN + 2
	def __init__(self, appFont: QFont):
		super().__init__()
		self.dragPosition = None
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.editor = EditorQt()
		self.editor.qtWindow = self
		self.appFont = appFont

		margin = self.CONTENT_MARGIN

		root = QWidget()
		root.setStyleSheet("background: black;")
		rootLayout = QVBoxLayout(root)
		rootLayout.setContentsMargins(margin, margin, margin, margin)
		rootLayout.setSpacing(0)

		self.titleBar = TitleBar("QUIVER", appFont, parent=root)

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
		for sig in (
			self.editor.signals.cursorMoved,
			self.editor.signals.changed,
			self.editor.signals.statusChanged
		):
			sig.connect(lambda *_: self.statusBarWidget.updateState(self.editor))
		
		rootLayout.addWidget(self.titleBar)
		rootLayout.addWidget(self.tabBar)
		rootLayout.addWidget(splitter, stretch=1)
		rootLayout.addWidget(self.statusBarWidget)
		self.setCentralWidget(root)

		self.border = BorderOverlay(root)
		self.border.raise_()

		self.setWindowTitle("QUIVER")
		self.setWindowIcon(QIcon("assets/icons/quiver.png"))
		self.resize(1280, 720)
		self.setMinimumSize(800, 550)

		self.statusBarWidget.updateState(self.editor)
		self.views.setFocus()
	
	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			titleBarBottom = self.titleBar.mapTo(self, self.titleBar.rect().bottomLeft()).y()
			if event.position().y() <= titleBarBottom:
				self.dragPosition = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
		super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if self.dragPosition is not None and event.buttons() == Qt.MouseButton.LeftButton:
			self.move(event.globalPosition().toPoint() - self.dragPosition)
		super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		self.dragPosition = None
		super().mouseReleaseEvent(event)

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
			names = ", ".join(unsaved)
			if not QuiverDialog.ask(
				"UNSAVED CHANGES",
				f"Wait! You haven't saved on\n{names}\n\nWould you still like to quit?",
				self.appFont, self
			):
				event.ignore()
				return
		event.accept()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		if hasattr(self, "border"):
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

	def focusExplorer(self):
		if self.explorer.isVisible():
			self.explorer.listWidget.setFocus()
		else:
			self.editor.showExplorer = True
			self.explorer.syncVisibility()
			self.explorer.listWidget.setFocus()

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