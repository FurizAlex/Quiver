#app.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PyQt6.QtCore import Qt, pyqtSignal

from frontend.qt.qtTheme import loadQtTheme
from frontend.qt.editorQt import EditorQt
from frontend.qt.docsViewer import DocsOverlay

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter, QSplitterHandle, QHBoxLayout, QPushButton, QLabel, QDialog
from PyQt6.QtGui import QFontDatabase, QFont, QFontMetrics, QPainter, QColor, QPen, QIcon
from frontend.qt.statusBar import StatusBar
from frontend.qt.editorView import EditorView
from frontend.qt.explorer import Explorer
from frontend.qt.tabBar import TabBar

def loadAppFont():
	fontID = QFontDatabase.addApplicationFont("assets/fonts/Courier New.ttf")
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
	dragRequest = pyqtSignal(object)
	def __init__(self, title: str, font: QFont, editor, parent=None):
		super().__init__(parent)
		self.dragPosition = None
		self.setFixedHeight(QFontMetrics(font).height() + 14)
		self.setMouseTracking(True)

		layout = QHBoxLayout(self)
		layout.setContentsMargins(8, 0, 4, 0)
		layout.setSpacing(0)

		self.titleLabel = QLabel(title)
		self.titleLabel.setFont(font)
		self.titleLabel.setStyleSheet("color: white; background: transparent;")
		self.titleLabel.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

		self.buttonMin		= self.makeButton("#CCCC00", self.minimize)
		self.buttonMax		= self.makeButton("#00CC00", self.maximize)
		self.buttonClose	= self.makeButton("#CC0000", self.closeWindow)

		editor.signals.changed.connect(self.update)

		layout.addWidget(self.titleLabel)
		layout.addStretch()
		layout.addWidget(self.buttonMin)
		layout.addSpacing(4)
		layout.addWidget(self.buttonMax)
		layout.addSpacing(4)
		layout.addWidget(self.buttonClose)
		layout.addSpacing(4)

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			localPos = event.position().toPoint()
			for button in (self.buttonMin, self.buttonMax, self.buttonClose):
				buttonRect = button.geometry()
				buttonRect.translate(0, 0)
				if button.geometry().contains(localPos):
					event.ignore()
					return
			event.ignore()
		else:
			event.ignore()

	def mouseMoveEvent(self, event):
		event.ignore()

	def mouseReleaseEvent(self, event):
		event.ignore()

	def makeButton(self, color: str, slot) -> QPushButton:
		button = QPushButton()
		button.setFixedSize(20, 20)
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

	def closeWindow(self):
		self.window().close()

	def paintEvent(self, event):
		painter = QPainter(self)
		from frontend.qt.amigaPalette import getColor
		painter.fillRect(self.rect(), QColor(getColor("STATUS_BG")))
		painter.setPen(QColor("#FFFFFF"))
		painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

	def mouseDoubleClickEvent(self, event):
		self.maximize()
		event.accept()

class QuiverDialog(QDialog):
	def __init__(self, title: str, message: str, font: QFont, parent=None, showSave: bool = False):
		super().__init__(parent, Qt.WindowType.FramelessWindowHint)
		self.setModal(True)
		self.outcome = "no"
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
		buttonRow.addStretch()

		def makeButton(text, foreground, background, callback):
			button = QPushButton(text)
			button.setFont(font)
			button.setFixedHeight(font.pointSize() * 3)
			button.setMinimumWidth(80)
			button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
			button.setStyleSheet(
				f"QPushButton {{ background: {background}; color: {foreground}; border: none; }}"
				f"QPushButton:hover {{ background: {paletteFg}; color: {paletteBg}; }}"
			)
			button.clicked.connect(callback)
			return button

		buttonNo	= makeButton("NO", paletteBg, paletteFg, self.no)
		buttonYes	= makeButton("YES", paletteBg, paletteFg, self.yes)
		buttonRow.addWidget(buttonNo)

		if showSave:
			buttonSave = makeButton("YES + SAVE", paletteBg, titleFg, self.save)
			buttonRow.addWidget(buttonSave)
		
		buttonRow.addWidget(buttonYes)

		boxLayout.addWidget(titleLabel)
		boxLayout.addWidget(msgLabel)
		boxLayout.addSpacing(4)
		boxLayout.addLayout(buttonRow)
		outer.addWidget(box)

		self.setFixedWidth(440)
		self.adjustSize()
	
	def yes(self):
		self.outcome = "yes"
		self.accept()

	def no(self):
		self.outcome = "no"
		self.reject()

	def save(self):
		self.outcome = "save"
		self.accept()

	@staticmethod
	def ask(title: str, message: str, font: QFont, parent=None, showSave=False):
		dialog = QuiverDialog(title, message, font, parent, showSave)
		if parent:
			geo = parent.geometry()
			dialog.move(
				geo.x() + (geo.width() - dialog.width()) // 2,
				geo.y() + (geo.height() - dialog.height()) // 2
			)
		dialog.exec()
		return dialog.outcome

class MainWindow(QMainWindow):
	CONTENT_MARGIN = BorderOverlay.MARGIN + 2
	RESIZE_MARGIN = 14
	def __init__(self, appFont: QFont):
		super().__init__()
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.editor = EditorQt()
		self.editor.qtWindow = self
		self.appFont = appFont

		self.dragging = False
		self.dragOffset = None

		self.resizing = False
		self.resizeDir = None
		self.resizeStart = None
		self.resizeGeo = None
		self.setMouseTracking(True)

		margin = self.CONTENT_MARGIN

		root = QWidget()
		root.setStyleSheet("background: black;")
		rootLayout = QVBoxLayout(root)
		rootLayout.setContentsMargins(margin, margin, margin, margin)
		rootLayout.setSpacing(0)

		self.titleBar = TitleBar("QUIVER", appFont, self.editor, parent=root)

		self.explorer = Explorer(self.editor, appFont)
		self.explorer.rebuild()

		self.tabBar = TabBar(self.editor, appFont)
		self.views = EditorView(self.editor, appFont)

		self.docsOverlay = DocsOverlay(self.editor, appFont, parent=root)
		self.docsOverlay.hide()

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

		self.editor.signals.changed.connect(self.updateWindowTitle)
		self.statusBarWidget.updateState(self.editor)
		self.views.setFocus()

	def positionDocsOverlay(self):
		titleBottom = self.titleBar.y() + self.titleBar.height()
		rootSize = self.centralWidget().size()
		self.docsOverlay.move(0, titleBottom)
		self.docsOverlay.resize(rootSize.width(), rootSize.height() - titleBottom)

	def applyQtTheme(self, themeDef: dict):
		self.editor.themeDither = themeDef.get("dither", False)
		from frontend.qt.amigaPalette import getColor
		explorerBg			= getColor("EXPLORER_BG")
		explorerFg			= getColor("EXPLORER_FG")
		explorerSelectBg	= getColor("EXPLORER_SELECT_BG")
		explorerSelectFg	= getColor("EXPLORER_SELECT_FG")

		for view in self.views.paneContainer.paneViews:
			view.backgroundImage = None
			view.backgroundImageSize = None
			view.backgroundImagePath = None
			view.gutterImage = None
			view.gutterImageSize = None

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
		self.titleBar.update()
		self.statusBarWidget.update()
		self.editor.notifyChanged()

	def closeEvent(self, event):
		unsaved = [b for b in self.editor.buffers if b.modified]
		if unsaved:
			names = ", ".join(b.name for b in unsaved)
			outcome = QuiverDialog.ask(
				"UNSAVED CHANGES",
				f"Wait! You haven't saved on\n{names}\n\nWould you still like to quit?",
				self.appFont, self,
				showSave=True
			)
			if outcome == "no":
				event.ignore()
				return
			if outcome == "save":
				from commands.fileCommands import save
				for buffer in unsaved:
					if buffer.filename:
						from util.fileio import saveFile
						saveFile(buffer.filename, buffer.lines)
						buffer.modified = False
					else:
						self.editor.pane.buffer = buffer
						save(self.editor)
		event.accept()

	def resizeDirection(self, globalPos):
		geo = self.frameGeometry()
		x, y = globalPos.x() - geo.x(), globalPos.y() - geo.y()
		w, h = geo.width(), geo.height()
		m = self.RESIZE_MARGIN
		left	= x < m
		right	= x > w - m
		top		= y < m
		bottom	= y > h - m
		if not any([left, right, top, bottom]):
			return None
		return (
			-1 if left else (1 if right else 0),
			-1 if top else (1 if bottom else 0)
		)

	def resizeEvent(self, event):
		super().resizeEvent(event)
		if hasattr(self, "border"):
			self.border.resize(self.centralWidget().size())
			self.border.raise_()
		if hasattr(self, "docsOverlay"):
			self.positionDocsOverlay()

	def showEvent(self, event):
		super().showEvent(event)
		self.border.resize(self.centralWidget().size())
		self.border.raise_()
		self.views.paneContainer.paneViews[0].setFocus()

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			direction = self.resizeDirection(event.globalPosition().toPoint())
			if direction is not None and direction != (0, 0):
				self.resizing = True
				self.resizeDir = direction
				self.resizeStart = event.globalPosition().toPoint()
				self.resizeGeo = self.frameGeometry()
				event.accept()
				return
			titleBottom = self.CONTENT_MARGIN + self.titleBar.height()
			if event.position().y() < titleBottom:
				self.windowHandle().startSystemMove()
				event.accept()
				return
		super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
			delta = event.globalPosition().toPoint() - self.resizeStart
			geo = self.resizeGeo
			dx, dy = self.resizeDir
			x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
			if dx == -1:
				newW = max(self.minimumWidth(), w - delta.x())
				newX = x + w - newW
			elif dx == 1:
				newW = max(self.minimumWidth(), w + delta.x())
				newX = x
			else:
				newW = w
				newX = x

			if dy == -1:
				newH = max(self.minimumHeight(), h - delta.y())
				newY = y + h - newH
			elif dy == 1:
				newH = max(self.minimumHeight(), h + delta.y())
				newY = y
			else:
				newH = h
				newY = y
			self.setGeometry(newX, newY, newW, newH)
			event.accept()
			return
		direction = self.resizeDirection(event.position().toPoint())
		if direction:
			dx, dy = direction
			if dx != 0 and dy != 0:
				self.setCursor(Qt.CursorShape.SizeFDiagCursor if dx == dy else Qt.CursorShape.SizeBDiagCursor)
			elif dx != 0:
				self.setCursor(Qt.CursorShape.SizeHorCursor)
			else:
				self.setCursor(Qt.CursorShape.SizeVerCursor)
		else:
			self.unsetCursor()
		super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		self.dragging = False
		self.resizing = False
		self.resizeDir = None
		self.unsetCursor()
		super().mouseReleaseEvent(event)

	def newFileQt(self):
		if self.pane.buffer.modified:
			outcome = QuiverDialog.ask(
			"UNSAVED CHANGES",
			f"'{self.pane.buffer.name}' has unsaved changes. Would you like to create a new file anyway?",
			self.appFont, self
			)
			if outcome != "yes":
				return
		from core.buffer import Buffer
		buffer = Buffer(editor=self, language=self.languageRegistry.get("text"))
		self.editor.buffers.append(buffer)
		self.editor.currentBuffer = len(self.editor.buffers) - 1
		self.editor.pane.buffer = buffer
		self.editor.pane.cursorX = 0
		self.editor.pane.cursorY = 0
		self.editor.notifyChanged()

	def openDocs(self):
		self.positionDocsOverlay()
		self.docsOverlay.raise_()
		self.docsOverlay.show()

	def focusExplorer(self):
		self.editor.showExplorer = True
		self.explorer.syncVisibility()
		self.explorer.rebuild()
		self.explorer.listWidget.setFocus()
		if self.explorer.listWidget.count() > 0:
			self.explorer.listWidget.setCurrentRow(0)

	def updateWindowTitle(self):
		buffer		= self.editor.pane.buffer
		name		= buffer.name if buffer.name else "untitled"
		modified	= " *" if buffer.modified else ""
		self.setWindowTitle(f"{name}{modified} - QUIVER")
		self.titleBar.titleLabel.setText(f"QUIVER | {name}{modified}")

if __name__ == "__main__":
	app = QApplication(sys.argv)
	appFont = loadAppFont()
	app.setFont(appFont)
	app.setStyleSheet(loadQtTheme("quiver"))
	icon = QIcon("assets/icons/quiver.png")
	app.setWindowIcon(icon)
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
	window.setWindowIcon(icon)
	window.show()
	window.editor.resize(window.width(), window.height())
	sys.exit(app.exec())