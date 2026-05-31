import curses

from input.event import InputEvent

def translate(raw):
	if raw == curses.KEY_UP:
		return InputEvent("UP")
	if raw == curses.KEY_DOWN:
		return InputEvent("DOWN")
	if raw == curses.KEY_LEFT:
		return InputEvent("LEFT")
	if raw == curses.KEY_RIGHT:
		return InputEvent("RIGHT")

	if raw == curses.KEY_HOME:
		return InputEvent("HOME")
	if raw == curses.KEY_END:
		return InputEvent("END")
	if raw == curses.KEY_PPAGE:
		return InputEvent("PAGEUP")
	if raw == curses.KEY_NPAGE:
		return InputEvent("PAGEDOWN")

	if raw == 10:
		return InputEvent("ENTER")
	if raw == 9:
		return InputEvent("TAB")
	if raw == 27:
		return InputEvent("ESC")
	if raw in (127, 8, curses.KEY_BACKSPACE):
		return InputEvent("BACKSPACE")
	if raw == curses.KEY_DC:
		return InputEvent("DELETE")
	if raw == curses.KEY_IC:
		return InputEvent("INSERT")
	
	if raw == curses.KEY_SLEFT:
		return InputEvent("SHIFT_LEFT", shift=True)
	if raw == curses.KEY_SRIGHT:
		return InputEvent("SHIFT_RIGHT", shift=True)
	if raw == curses.KEY_MOUSE:
		return InputEvent("MOUSE")
	
	if 1 <= raw <= 26:
		letter = chr(raw + 64)
		return InputEvent(letter, ctrl=True)
	if 32 <= raw <= 126:
		return InputEvent(chr(raw))
	return InputEvent(f"KEY_{raw}")