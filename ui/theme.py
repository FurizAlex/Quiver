import curses

class Theme:
	def __init__(self):
		self.colors = {
			"keyword": curses.COLOR_CYAN,
			"string": curses.COLOR_GREEN,
			"comment": curses.COLOR_YELLOW,
			"text": curses.COLOR_WHITE,
			"status": curses.COLOR_BLUE
		}
	
	def initialize(self):
		curses.start_color()
		curses.use_default_colors()

		curses.init_pair(1, self.colors["keyword"], -1)
		curses.init_pair(2, self.colors["string"], -1)
		curses.init_pair(3, self.colors["comment"], -1)
		curses.init_pair(4, self.colors["text"], -1)
		curses.init_pair(5, curses.COLOR_BLACK, self.colors["status"])