import curses
import signal
import os

from core.buffer import Buffer
from core.cursor import Cursor
from core.history import History
from ui.renderer import Renderer

from core.selection import Selection
from core.clipboard import Clipboard

from config.settings import Settings
from input.visualMode import handle as handleVisual

from ui.pane import Pane
from ui.theme import Theme

from input.commandMode import handle as handleCommand

class Editor:
	def __init__(self, stdscr):
		self.stdscr = stdscr

		curses.cbreak()
		curses.noecho()
		curses.curs_set(1)

		stdscr.keypad(True)
		curses.mousemask(curses.ALL_MOUSE_EVENTS)
		stdscr.timeout(16)

		curses.start_color()
		curses.use_default_colors()

		signal.signal(signal.SIGTSTP, signal.SIG_IGN)

		self.buffers = [Buffer()]
		self.currentBuffer = 0
		self.history = History()

		self.panes = [Pane(0)]
		self.activePane = 0

		self.statusTimer = 0

		self.selection = Selection()
		self.clipboard = Clipboard()

		self.settings = Settings()
		self.theme = Theme()
		self.theme.load("amiga")
		self.theme.initialize()
		self.renderer = Renderer(stdscr)

		self.showExplorer = True
		self.explorerWidth = 30
		self.explorerPath = "."
		self.explorerFiles = []
		self.selectedFileIndex = 0

		self.paletteOpen = False
		self.paletteInput = ""
		self.paletteMode = "commands"
		self.paletteItems = [
			"open",
			"save",
			"quit",
			"theme",
			"explorer",
			"new buffer"
		]
		self.paletteSelection = 0

		self.mode = "INSERT"
		self.focus = "editor"
		self.running = True
		self.filename = None
		self.status = "WELCOME TO QUIVER"

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
			key = self.stdscr.getch()
			self.handleInput(key)

	def handleInput(self, key):
		from input.insertMode import handle
		from input.paletteMode import handle as handlePalette

		if key  == curses.KEY_MOUSE:
			from input.mouseMode import handle
			handle(self)
			return
		if self.paletteOpen:
			try:
				handlePalette(self, key)
			except Exception as e:
				self.paletteOpen = False
				self.status = str(e)
			return
		if self.focus == "explorer":
			from input.explorerMode import handle
			handle(self, key)
			return
		if self.saving:
			from input.saveMode import handle

			handle(self, key)
			return
		handle(self, key)

	def updateScroll(self):
		h, _ = self.stdscr.getmaxyx()

		if self.pane.cursorY < self.pane.scrollY:
			self.pane.scrollY = self.pane.cursorY

		elif self.pane.cursorY >= self.pane.scrollY + h - 1:
			self.pane.scrollY = self.pane.cursorY - (h - 2)

	def refreshExplorer(self):
		try:
			self.explorerFiles = sorted(os.listdir(self.explorerPath))
		except:
			self.explorerFiles = []

	@property
	def buffer(self):
		return self.buffers[self.currentBuffer]

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