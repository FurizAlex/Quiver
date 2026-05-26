from core.buffer import Buffer
from core.cursor import Cursor
from core.history import History
from ui.renderer import Rendeder

class Editor:
	def __init__(self, stdscr):
		self.stdscr = stdscr
		self.buffer = Buffer()
		self.cursor = Cursor()
		self.history = History()

		self.mode = "NORNAL"
		self.running = True
		self.filename = None
		self.status = "WELCOME TO QUIVER"

		self.scrollY = 0
		self.scrollX = 0

		self.renderer = Rendeder(stdscr)
	
	def run(self):
		while self.running:
			self.renderer.draw(self)
			key = self.stdscr.getch()
			self.handleInput(key)

	def handleInput(self, key):
		if self.mode == "NORMAL":
			self.handleNormal(key)
		elif self.mode == "EDIT":
			self.handleEdit(key)
		elif self.mode == "COMMAND":
			self.handleCommand(key)