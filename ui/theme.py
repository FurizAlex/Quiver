import os
import curses
import importlib

COLOR_MAP = {
	"black": curses.COLOR_BLACK,
	"red": curses.COLOR_RED,
	"green": curses.COLOR_GREEN,
	"yellow": curses.COLOR_YELLOW,
	"blue": curses.COLOR_BLUE,
	"magenta": curses.COLOR_MAGENTA,
	"cyan": curses.COLOR_CYAN,
	"white": curses.COLOR_WHITE,

	"default": -1
}

class Theme:
	def __init__(self):
		self.colors = {}
		self.definition = {}

		self.nextPair = 1
		self.pairs = {}

	def color(self, name):
		return COLOR_MAP.get(name, -1)
	
	def load(self, name):
		module = importlib.import_module(f"themes.{name}")
		self.definition = module.THEME
	
	def getPair(self, fg, bg):
		key = (fg, bg)

		if key not in self.pairs:
			curses.init_pair(self.nextPair, fg, bg)

			self.pairs[key] = curses.color_pair(self.nextPair)
			self.nextPair += 1
		return self.pairs[key]

	def availableThemes(self):
		themes = []

		for file in os.listdir("themes"):
			if file.endswith(".py") and not file.startswith("___"):
				moduleName = file[:-3]

				try:
					module = importlib.import_module(f"themes.{moduleName}")
					meta = module.THEME.get("meta", {})
					themes.append({
						"id": moduleName,
						"name": meta.get("name", moduleName),
						"author": meta.get("author", ""),
						"version": meta.get("version", "")
					})
				except Exception:
					pass
		return themes

	def initialize(self):
		self.colors = {}
		self.nextPair = 1
		self.pairs = {}
		
		default = self.definition.get("defaults", {})
		default_fg = self.color(default.get("fg", "default"))
		default_bg = self.color(default.get("bg", "default"))

		default_attr = self.getPair(default_fg, default_bg)

		for token, style in self.definition.items():
			if token in ("meta", "defaults"):
				continue
			
			fg = self.color(style.get("fg", default.get("fg", "default")))
			bg = self.color(style.get("bg", default.get("bg", "default")))

			attr = self.getPair(fg, bg)

			if style.get("bold"):
				attr |= curses.A_BOLD
			if style.get("dim"):
				attr |= curses.A_DIM
			if style.get("reverse"):
				attr |= curses.A_REVERSE
			if style.get("underline"):
				attr |= curses.A_UNDERLINE
			self.colors[token] = attr
		self.default_attr = default_attr

	def get(self, key):
		return self.colors.get(key, self.default_attr)

	@property
	def metadata(self):
		return self.definition.get("meta", {})