palette = {
	"BACKGROUND"			: "#000000",
	"GUTTER"				: "#0000AA",
	"GUTTER_SEP"			: "#FFFFFF",
	"TEXT"					: "#FFFFFF",
	"KEYWORD"				: "#FFFF55",
	"STRING"				: "#55FFFF",
	"COMMENT"				: "#AAAAAA",
	"NUMBER"				: "#FFFF55",
	"CURSOR"				: "#00FF00",
	"SELECTION"				: "#FFFFFF",
	"SELECTION_TEXT"		: "#0000AA",
	"CURRENT_LINE"			: "#0000AA",
	"STATUS_BG"				: "#0000AA",
	"STATUS_FG"				: "#FFFFFF",
	"PALETTE_BG"			: "#0000AA",
    "PALETTE_FG"			: "#FFFFFF",
    "PALETTE_SELECT_BG"		: "#FFFFFF",
    "PALETTE_SELECT_FG"		: "#0000AA",
    "PALETTE_TITLE"			: "#FFFF55",
    "PALETTE_HINT"			: "#AAAAAA",
	"EXPLORER_BG"			: "#0000AA",
	"EXPLORER_FG"			: "#FFFFFF",
	"EXPLORER_SELECT_BG"	: "#FFFFFF",
	"EXPLORER_SELECT_FG"	: "#0000AA",
	"TAB_BG"				: "#0000AA",
	"TAB_FG"				: "#FFFFFF",
	"TAB_ACTIVE_BG"			: "#000033",
	"TAB_ACTIVE_FG"			: "#FFFFFF",
}

CURSES_TO_HEX = {
	"black":		"#000000",
	"red":			"#CC0000",
	"lime":			"#00FF00",
	"green":		"#00CC00",
	"dark green":	"#087000",
	"yellow":		"#CCCC00",
	"blue":			"#0000AA",
	"aqua":			"#05696B",			
	"magenta":		"#AA00AA",
	"cyan":			"#00AAAA",
	"white":		"#FFFFFF",
	"grey":			"#D1D1D1",
	"default":		"#FFFFFF",
}

def getColor(key: str) -> str:
	return palette.get(key, "#FFFFFF")

def applyThemeToQt(themeDefinition: dict):
	defaults = themeDefinition.get("defaults", {})
	bg = CURSES_TO_HEX.get(defaults.get("bg", "black"), "#000000")
	fg = CURSES_TO_HEX.get(defaults.get("fg", "white"), "#FFFFFF")

	def foreground(token, fallback=None):
		style = themeDefinition.get(token, {})
		return CURSES_TO_HEX.get(style.get("fg", defaults.get("fg", "white")), fallback or fg)
	
	def background(token, fallback=None):
		style = themeDefinition.get(token, {})
		return CURSES_TO_HEX.get(style.get("bg", defaults.get("bg", "black")), fallback or bg)
	
	palette["BACKGROUND"]			= bg
	palette["TEXT"]					= fg
	palette["KEYWORD"]				= foreground("keyword")
	palette["STRING"]				= foreground("string")
	palette["COMMENT"]				= foreground("comment")
	palette["NUMBER"]				= foreground("number")

	palette["GUTTER"]				= background("lineNumber", bg)
	palette["GUTTER_SEP"]			= foreground("lineNumber", fg)

	palette["CURRENT_LINE"]			= background("lineNumber", bg)

	palette["SELECTION"]			= foreground("selection", fg)
	palette["SELECTION_TEXT"]		= background("selection", bg)

	palette["STATUS_BG"]			= background("statusBar", bg)
	palette["STATUS_FG"]			= foreground("statusBar", fg)

	palette["PALETTE_BG"]			= background("paletteBorder", "#000000")
	palette["PALETTE_FG"]			= foreground("paletteItem", fg)
	palette["PALETTE_SELECT_BG"]	= background("paletteSelection", fg)
	palette["PALETTE_SELECT_FG"]	= foreground("paletteSelection", bg)
	palette["PALETTE_TITLE"]		= foreground("paletteTitle", fg)
	palette["PALETTE_HINT"]			= foreground("comment", fg)

	palette["EXPLORER_BG"]			= background("explorerItem", fg)
	palette["EXPLORER_FG"]			= foreground("explorerItem", bg)
	palette["EXPLORER_SELECT_BG"]	= background("explorerSelection", bg)
	palette["EXPLORER_SELECT_FG"]	= foreground("explorerSelection", fg)

	palette["TAB_BG"]           	= background("tab", bg)
	palette["TAB_FG"]           	= foreground("tab", fg)
	palette["TAB_ACTIVE_BG"]    	= background("activeTab", bg)
	palette["TAB_ACTIVE_FG"]    	= foreground("activeTab", fg)
	palette["CURSOR"]				= "#00FF00"