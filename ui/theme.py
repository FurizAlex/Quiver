import curses
import importlib

class Theme:
	def __init__(self):
		self.colors = {}
	
	def load(self, name):
		if name == "amiga":
			self.colors = {
				"text": curses.color_pair(1),
				"keyword": curses.color_pair(2),
				"string": curses.color_pair(3),
				"comment": curses.color_pair(4),

				"cursorline": curses.A_DIM | curses.color_pair(1),
				"selection": curses.A_REVERSE,

				"lineNumber": curses.A_DIM,
				"statusBar": curses.A_REVERSE,
			}

	def initialize(self):
		curses.start_color()
		curses.use_default_colors()

		curses.init_pair(1, curses.COLOR_WHITE, -1)
		curses.init_pair(2, curses.COLOR_CYAN, -1)
		curses.init_pair(3, curses.COLOR_YELLOW, -1)
		curses.init_pair(4, curses.COLOR_GREEN, -1)

	def get(self, key):
		return self.colors.get(key, curses.A_NORMAL)