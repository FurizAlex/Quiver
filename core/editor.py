import curses

from core.buffer import Buffer
from core.cursor import Cursor
from core.history import History
from ui.renderer import Renderer

from core.selection import Selection
from core.clipboard import Clipboard

from config.settings import Settings
from input.visualMode import handle as handleVisual

from ui.theme import Theme

from input.normalMode import handle as handleNormal
from input.editMode import handle as handleEdit
from input.commandMode import handle as handleCommand

class Editor:
	def __init__(self, stdscr):
		self.stdscr = stdscr

		curses.raw()
		curses.noecho()
		curses.curs_set(1)

		stdscr.keypad(True)

		curses.start_color()
		curses.use_default_colors()

		curses.init_pair(1, curses.COLOR_CYAN, -1)
		curses.init_pair(2, curses.COLOR_GREEN, -1)
		curses.init_pair(3, curses.COLOR_YELLOW, -1)
		curses.init_pair(4, curses.COLOR_WHITE, -1)
		curses.init_pair(5, curses.COLOR_BLACK, -1)

		self.buffer = Buffer()
		self.cursor = Cursor()
		self.history = History()

		self.selection = Selection()
		self.clipboard = Clipboard()

		self.settings = Settings()
		self.theme = Theme()
		self.theme.initialize()
		self.renderer = Renderer(stdscr)

		self.mode = "NORMAL"
		self.running = True
		self.filename = None
		self.status = "WELCOME TO QUIVER"

		self.command = ""

		self.scrollY = 0
		self.scrollX = 0
	
	def run(self):
		while self.running:
			self.updateScroll()
			self.renderer.draw(self)
			key = self.stdscr.getch()
			self.handleInput(key)

	def handleInput(self, key):
		if self.mode == "NORMAL":
			handleNormal(self, key)
		elif self.mode == "EDIT":
			handleEdit(self, key)
		elif self.mode == "COMMAND":
			handleCommand(self, key)
		elif self.mode == "VISUAL":
			handleVisual(self, key)

	def updateScroll(self):
		h, _ = self.stdscr.getmaxyx()

		if self.cursor.y < self.scrollY:
			self.scrollY = self.cursor.y

		elif self.cursor.y >= self.scrollY + h - 1:
			self.scrollY = self.cursor.y - (h - 2)