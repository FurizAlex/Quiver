import curses
import signal
import os

from core.buffer import Buffer
from core.cursor import Cursor
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
	def __init__(self, stdscr):
		self.stdscr = stdscr

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

		self.panes = [Pane(0)]
		self.activePane = 0

		self.statusTimer = 0

		self.selection = Selection()
		self.clipboard = Clipboard()

		self.settings = Settings()
		self.config = ConfigManager()
		self.config.load()

		self.settings.load(self.config.get("settings", {}))

		self.theme = Theme()
		self.currentTheme = self.settings.get("theme")
		self.theme.load(self.currentTheme)
		self.plugins = PluginManager()
		self.theme.initialize()
		self.layout = Layout(self)
		self.renderer = Renderer(stdscr)

		self.languageRegistry = LanguageRegistry()
		registerLanguages(self.languageRegistry)

		from core.documentManager import DocumentManager
		self.documents = DocumentManager(self.languageRegistry)

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
				self.running = False
				raise

	def handleInput(self, event):
		self.status = (
			f"KEY={event.key} "
			f"CTRL={event.ctrl}"
		)
		if event.key == curses.KEY_MOUSE:
			from input.mouseMode import handleMouse

			handleMouse(self)
			return
		from input.registry import INPUT_HANDLERS

		self.plugins.dispatchKey(self, event)

		if self.paletteOpen:
			self.mode = "PALETTE"
		elif self.saving:
			self.mode = "SAVE"
		elif self.focus == "explorer":
			self.mode = "EXPLORER"
		elif self.searchMode:
			self.mode = "SEARCH"
		else:
			self.mode = "INSERT"
		handler = INPUT_HANDLERS.get(self.mode)

		if handler:
			handler(self, event)

	def updateScroll(self):
		h, w = self.stdscr.getmaxyx()

		pane = self.pane
		visibleHeight = (self.layout.paneVisibleHeight())

		if pane.cursorY < pane.scrollY:
			pane.scrollY = pane.cursorY
		elif pane.cursorY >= (pane.scrollY + self.layout.paneVisibleHeight()):
			pane.scrollY = (pane.cursorY - self.layout.paneVisibleHeight() + 1)
		
		visibleWidth = (self.layout.paneWidth() - self.layout.lineNumberWidth - 2)
		
		if pane.cursorX < pane.scrollX:
			pane.scrollX = pane.cursorX
		elif pane.cursorX >= (pane.scrollX + visibleWidth):
			pane.scrollX = (pane.cursorX - visibleWidth + 1)

	def refreshExplorer(self):
		try:
			self.explorerFiles = sorted(os.listdir(self.explorerPath))
		except:
			self.explorerFiles = []

	def saveConfig(self):
		self.config.set("settings", self.settings.export())
		self.config.save()

	@property
	def buffer(self):
		index = self.pane.bufferIndex
		
		#if index >= len(self.buffers):
		#	print("BUFFER DESYNC:", "pane.bufferIndex =", index, "Buffers =", len(self.buffers))
		self.pane.bufferIndex = max(0, len(self.buffers) - 1)
		return self.buffers[self.pane.bufferIndex]

	@property
	def pane(self):
		return self.panes[self.activePane]

	@property
	def cursor(self):
		return self.pane

	@property
	def scrollY(self):
		return self.pane.scrollY

	@scrollY.setter
	def scrollY(self, value):
		self.pane.scrollY = value

	@property
	def scrollX(self):
		return self.pane.scrollX

	@scrollX.setter
	def scrollX(self, value):
		self.pane.scrollX = value

	@property
	def buffers(self):
		return self.documents.buffers
	
	@property
	def currentBuffer(self):
		return self.documents.current

	@currentBuffer.setter
	def currentBuffer(self, value):
		self.documents.current = value

	@property
	def activeBuffer(self):
		return self.documents.active