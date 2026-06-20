import signal
import os

from core.buffer import Buffer
from core.cursor import Cursor
from core.multiSelection import MultiSelection
from core.history import History
from ui.renderer import Renderer

from config.configManager import ConfigManager
from core.commandRegistry import CommandRegistry
from commands.registerCommands import registerCommands

from core.selection import Selection
from core.clipboard import Clipboard
from core.pluginManager import PluginManager

from config.settings import Settings
from input.visualMode import handle as handleVisual

from ui.layout import Layout
from ui.pane import Pane
from ui.theme import Theme

from input.commandMode import handle as handleCommand

from syntax.languageRegistry import LanguageRegistry
from syntax.registerLanguages import registerLanguages

class Editor:
	def __init__(self, stdscr=None):
		self.stdscr = stdscr

		if stdscr is not None:
			import curses
			curses.cbreak()
			curses.noecho()
			curses.curs_set(1)
			stdscr.keypad(True)
			curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
			stdscr.timeout(16)
			curses.start_color()
			curses.use_default_colors()

		signal.signal(signal.SIGTSTP, signal.SIG_IGN)

		self.history = History()
		self.commands = CommandRegistry()
		registerCommands(self.commands)

		self.statusTimer = 0

		self.selection = MultiSelection()
		self.clipboard = Clipboard()

		self.settings = Settings()
		self.config = ConfigManager()
		self.config.load()

		self.settings.load(self.config.get("settings", {}))

		self.theme = Theme()
		self.currentTheme = self.settings.get("theme")
		self.theme.load(self.currentTheme)
		if stdscr is not None:
			self.theme.initialize()
		self.plugins = PluginManager()
		self.layout = Layout(self)
		self.renderer = None
		if stdscr is not None:
			self.renderer = Renderer(stdscr)

		self.languageRegistry = LanguageRegistry()
		registerLanguages(self.languageRegistry)

		from core.documentManager import DocumentManager
		self.documents = DocumentManager(self, self.languageRegistry)

		from core.completion import CompletionEngine
		self.completion = CompletionEngine()
		self.completions = []
		self.completionIndex = 0
		self.completionActive = False
		
		self.panes = [Pane(self.documents.active)]
		self.activePane = 0

		self.showExplorer = self.settings.get("show_explorer")
		self.explorerWidth = 30
		self.explorerPath = "."
		self.explorerFiles = []
		self.selectedFileIndex = 0

		self.paletteOpen = False
		self.paletteInput = ""
		self.paletteMode = "commands"
		self.paletteItems = []
		self.paletteSelection = 0

		self.mode = "INSERT"
		self.focus = "editor"
		self.running = True
		self.filename = None
		self.status = "WELCOME TO QUIVER"

		self.gotoMode = False
		self.gotoInput = ""

		self.searchMode = False
		self.searchInput = ""

		self.saving = False
		self.saveInput = ""

		self.command = ""

		self.screenWidth = 80
		self.screenHeight = 25
		self.scrollY = 0
		self.scrollX = 0
		self.refreshExplorer()
	
	def run(self):
		while self.running:
			if self.statusTimer > 0:
				self.statusTimer -= 1

				if self.statusTimer == 0:
					self.status = ""
			self.updateScroll()
			self.renderer.draw(self)
			from input.translator import translate

			raw = self.stdscr.getch()
			event = translate(raw)
			try:
				self.handleInput(event)
			except Exception as e:
				self.status = f"ERROR: {e}"
				self.statusTimer = 180

	def handleInput(self, event):
		self.lastKeyDebug = f"KEY={event.key} CTRL={event.ctrl}"
		if event.key == "MOUSE":
			from input.mouseMode import handleMouse
			handleMouse(self, event)
			return
		from input.registry import INPUT_HANDLERS
		self.plugins.dispatchKey(self, event)

		if self.paletteOpen:
			self.mode = "PALETTE"
		elif self.saving:
			self.mode = "SAVE"
		elif self.gotoMode:
			self.mode = "GOTO"
		elif self.focus == "explorer":
			self.mode = "EXPLORER"
		elif self.searchMode:
			self.mode = "SEARCH"
		else:
			self.mode = "INSERT"
		handler = INPUT_HANDLERS.get(self.mode)
		if handler:
			handler(self, event)
		self.notifyStatusChanged()
		self.notifyCursorMoved()

	def updateScroll(self):
		pane = self.pane

		if hasattr(self, "signals"):
			visibleLines = max(1, getattr(pane, "visibleLines", 30))
			visibleCols = max(1, getattr(pane, "visibleCols", 80))
		else:
			visibleLines = self.layout.paneVisibleHeight()
			visibleCols = self.layout.paneWidth() - self.layout.lineNumberWidth - 2

		if pane.cursorY < pane.scrollY:
			pane.scrollY = pane.cursorY
		elif pane.cursorY >= pane.scrollY + visibleLines:
			pane.scrollY = pane.cursorY - visibleLines + 1
		
		if pane.cursorX < pane.scrollX:
			pane.scrollX = pane.cursorX
		elif pane.cursorX >= pane.scrollX + visibleCols:
			pane.scrollX = pane.cursorX - visibleCols + 1

	def refreshExplorer(self):
		try:
			self.explorerFiles = sorted(os.listdir(self.explorerPath))
		except:
			self.explorerFiles = []

	def saveConfig(self):
		self.config.set("settings", self.settings.export())
		self.config.save()

	def captureState(self):
		pane = self.panes[self.activePane]

		return {
			"lines": list(self.documents.active.lines),
			"cursorX": pane.cursorX,
			"cursorY": pane.cursorY
		}
	
	def resize(self, width, height):
		self.screenWidth = width
		self.screenHeight = height

	@property
	def pane(self):
		return self.panes[self.activePane]

	@property
	def buffers(self):
		return self.documents.buffers
	
	@property
	def currentBuffer(self):
		return self.documents.current

	@currentBuffer.setter
	def currentBuffer(self, value):
		self.documents.current = value

	def notifyChanged(self):
		pass

	def notifyCursorMoved(self):
		pass

	def notifyStatusChanged(self):
		pass

	def notifyPanesChanged(self):
		pass