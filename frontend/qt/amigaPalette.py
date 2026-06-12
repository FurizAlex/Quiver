BACKGROUND = "#000000"
GUTTER     = "#0000AA"
GUTTER_SEP = "#FFFFFF"
TEXT       = "#FFFFFF"
KEYWORD    = "#FFFF55"
STRING     = "#55FFFF"
COMMENT    = "#AAAAAA"
NUMBER     = "#FFFF55"
CURSOR     = "#00FF00"
SELECTION  = "#FFFFFF"
SELECTION_TEXT = "#0000AA"
CURRENT_LINE = "#0000AA"

CURSES_TO_HEX = {
	"black": "#000000",
	"red": "#CC0000",
	"green": "#00CC00",
	"yellow": "#CCCC00",
	"blue": "#0000AA",
	"magenta": "#AA00AA",
	"cyan": "#00AAAA",
	"white": "#FFFFFF",
	"default": "#FFFFFFF",
}

def applyThemeToQt(themeDefinition: dict):
	global BACKGROUND, GUTTER, TEXT, KEYWORD, STRING, COMMENT
	global CURSOR, SELECTION, CURRENT_LINE, GUTTER_SEP

	defaults = themeDefinition.get("default", {})
	bg = CURSES_TO_HEX.get(defaults.get("bg", "black"), "#000000")
	fg = CURSES_TO_HEX.get(defaults.get("fg", "white"), "#FFFFFF")

	BACKGROUND = bg
	TEXT = fg

	def foreground(token):
		style = themeDefinition.get(token, {})
		return CURSES_TO_HEX.get(style.get("fg", defaults.get("fg", "white")), fg)
	
	def background(token):
		style = themeDefinition.get(token, {})
		return CURSES_TO_HEX.get(style.get("bg", defaults.get("bg", "black")), bg)
	
	KEYWORD			= foreground("keyword")
	STRING			= foreground("string")
	COMMENT			= foreground("comment")
	GUTTER			= background("text") if background("text") != bg else "#0000AA"
	SELECTION		= background("selection") if "selection" in themeDefinition else "#FFFFFF"
	CURRENT_LINE	= background("keyword") if background("text") != bg else "#0000AA"