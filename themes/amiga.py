import curses

THEME = {
	"keyword": (
		curses.COLOR_CYAN,
		-1
	),
	"string": (
		curses.COLOR_GREEN,
		-1
	),
	"comment": (
		curses.COLOR_YELLOW,
		-1
	),
	"text": (
		curses.COLOR_WHITE,
		-1
	),
	"cursorline": (
		curses.COLOR_BLACK,
		curses.COLOR_CYAN
	),
	"statusbar": (
		curses.COLOR_BLACK,
		curses.COLOR_WHITE
	),
	"border": (
		curses.COLOR_CYAN,
		-1
	),
	"palette": (
		curses.COLOR_WHITE,
		curses.COLOR_BLUE
	),
	"selection": (
		curses.COLOR_BLACK,
		curses.COLOR_YELLOW
	)
}