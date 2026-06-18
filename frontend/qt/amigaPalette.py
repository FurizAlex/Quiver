from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QColor
from pathlib import Path
import numpy as np

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
	"DITHER"				: False,
	"GRADIENT"				: None,
	"BACKGROUND_IMAGE"		: None,
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
	"cyan":			"#008F8F",
	"white":		"#FFFFFF",
	"grey":			"#D1D1D1",
	"dark grey":	"#808080",
	"default":		"#FFFFFF",
}

BAYER_8X8 = np.array([
	[ 0,128, 32,160,  8,136, 40,168,  2,130, 34,162, 10,138, 42,170],
	[192, 64,224, 96,200, 72,232,104,194, 66,226, 98,202, 74,234,106],
	[ 48,176, 16,144, 56,184, 24,152, 50,178, 18,146, 58,186, 26,154],
	[240,112,208, 80,248,120,216, 88,242,114,210, 82,250,122,218, 90],
	[ 12,140, 44,172,  4,132, 36,164, 14,142, 46,174,  6,134, 38,166],
	[204, 76,236,108,196, 68,228,100,206, 78,238,110,198, 70,230,102],
	[ 60,188, 28,156, 52,180, 20,148, 62,190, 30,158, 54,182, 22,150],
	[252,124,220, 92,244,116,212, 84,254,126,222, 94,246,118,214, 86],
	[  3,131, 35,163, 11,139, 43,171,  1,129, 33,161,  9,137, 41,169],
	[195, 67,227, 99,203, 75,235,107,193, 65,225, 97,201, 73,233,105],
	[ 51,179, 19,147, 59,187, 27,155, 49,177, 17,145, 57,185, 25,153],
	[243,115,211, 83,251,123,219, 91,241,113,209, 81,249,121,217, 89],
	[ 15,143, 47,175,  7,135, 39,167, 13,141, 45,173,  5,133, 37,165],
	[207, 79,239,111,199, 71,231,103,205, 77,237,109,197, 69,229,101],
	[ 63,191, 31,159, 55,183, 23,151, 61,189, 29,157, 53,181, 21,149],
	[255,127,223, 95,247,119,215, 87,253,125,221, 93,245,117,213, 85],
], dtype=np.float32) / 256.0

def getColor(key: str) -> str:
	return palette.get(key, "#FFFFFF")

def ditherBlend(x: int, y: int, colorA: str, colorB: str, t: float) -> str:
	threshold = BAYER_8X8[y % 4][x % 4]
	return colorB if t > threshold else colorA

def buildDitherImage(w: int, h: int, stops: list) -> "QImage":
	img = QImage(w, h, QImage.Format.Format_RGB32)

	# This was hell to research just to let you know
	MATRIX = np.array([
		[ 0,128, 32,160,  8,136, 40,168,  2,130, 34,162, 10,138, 42,170],
		[192, 64,224, 96,200, 72,232,104,194, 66,226, 98,202, 74,234,106],
		[ 48,176, 16,144, 56,184, 24,152, 50,178, 18,146, 58,186, 26,154],
		[240,112,208, 80,248,120,216, 88,242,114,210, 82,250,122,218, 90],
		[ 12,140, 44,172,  4,132, 36,164, 14,142, 46,174,  6,134, 38,166],
		[204, 76,236,108,196, 68,228,100,206, 78,238,110,198, 70,230,102],
		[ 60,188, 28,156, 52,180, 20,148, 62,190, 30,158, 54,182, 22,150],
		[252,124,220, 92,244,116,212, 84,254,126,222, 94,246,118,214, 86],
		[  3,131, 35,163, 11,139, 43,171,  1,129, 33,161,  9,137, 41,169],
		[195, 67,227, 99,203, 75,235,107,193, 65,225, 97,201, 73,233,105],
		[ 51,179, 19,147, 59,187, 27,155, 49,177, 17,145, 57,185, 25,153],
		[243,115,211, 83,251,123,219, 91,241,113,209, 81,249,121,217, 89],
		[ 15,143, 47,175,  7,135, 39,167, 13,141, 45,173,  5,133, 37,165],
		[207, 79,239,111,199, 71,231,103,205, 77,237,109,197, 69,229,101],
		[ 63,191, 31,159, 55,183, 23,151, 61,189, 29,157, 53,181, 21,149],
		[255,127,223, 95,247,119,215, 87,253,125,221, 93,245,117,213, 85],
	], dtype=np.float32) / 256.0

	TILE = 16
	
	def hexToRgb(h):
		h = h.lstrip("#")
		return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)], dtype=np.float32)
	
	sortedStops = sorted(stops, key=lambda s: s[0])
	
	tVals = np.linspace(0.0, 1.0, h, dtype=np.float32)
	gradient = np.zeros((h, 3), dtype=np.float32)
	for i, t in enumerate(tVals):
		for j in range(len(sortedStops) - 1):
			p0, c0 = sortedStops[j]
			p1, c1 = sortedStops[j + 1]
			if p0 <= t <= p1:
				f = (t - p0) / max(p1 - p0, 1e-6)
				gradient[i] = hexToRgb(c0) * (1 - f) + hexToRgb(c1) * f
				break
		else:
			gradient[i] = hexToRgb(sortedStops[-1][1])
	
	matrixTiled = np.tile(MATRIX, (h // TILE + 1, w // TILE + 1))[:h, :w]

	DITHER_STRENGTH = 0.4
	tGrid = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, np.newaxis]
	tGrid = tGrid + (matrixTiled - 0.5) * DITHER_STRENGTH
	tGrid = np.clip(tGrid, 0.0, 1.0)

	pixelRows = (tGrid * (h - 1)).astype(np.int32)
	rgb = gradient[pixelRows]
	rgb = np.clip(rgb, 0, 255).astype(np.uint8)

	argb = np.zeros((h, w), dtype=np.uint32)
	argb[:] = (0xFF000000
		| (rgb[:,:,0].astype(np.uint32) << 16)
		| (rgb[:,:,1].astype(np.uint32) << 8)
		| rgb[:,:,2].astype(np.uint32))
	
	img = QImage(argb.tobytes(), w, h, w * 4, QImage.Format.Format_ARGB32)
	return img.copy()

def loadBackgroundImage(path: str, w: int, h: int) -> "QImage":
	fullPath = Path(path)
	if not fullPath.is_absolute():
		fullPath = Path(__file__).resolve().parents[2] / path
	img = QImage(str(fullPath))
	if img.isNull():
		return None
	return img.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)

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

	palette["DITHER"]   			= themeDefinition.get("dither", False)
	palette["GRADIENT"] 			= themeDefinition.get("gradient", None)
	palette["BACKGROUND_IMAGE"]		= themeDefinition.get("background_image", None)

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