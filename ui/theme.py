import curses
import importlib

class Theme:
	def __init__(self):
		self.current = "amiga"

		self.pairs = {}
		self.colors = {}
	
	def load(self, name):
		module = importlib.import_module(
			f"themes.{name}"
		)
		self.colors = module.THEME
		self.current = name

	def initialize(self):
		index = 1
		self.pairs.clear()

		for name, (fg, bg) in self.colors.items():
			curses.init_pair(
				index,
				fg,
				bg
			)
			self.pairs[name] = (
				curses.color_pair(index)
			)
			index += 1

	def setTheme(self, name):
		self.load(name)
		self.initialize()
	
	def get(self, name):
		return self.pairs.get(
			name,
			curses.A_NORMAL
		)