import curses

from input.event import InputEvent

def translateMouseState(state):
	import curses
	if state & curses.BUTTON1_PRESSED:
		return "LEFT_PRESS"
	if state & curses.BUTTON1_RELEASED:
		return "LEFT_RELEASE"
	if state & curses.BUTTON1_CLICKED:
		return "LEFT_CLICK"
	if state & curses.BUTTON4_PRESSED:
		return "WHEEL_UP"
	if state & curses.BUTTON5_PRESSED:
		return "WHEEL_DOWN"
	return "UNKNOWN"

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
	
	if raw == curses.KEY_MOUSE:
		try:
			_, mx, my, _, state = curses.getmouse()
			return InputEvent(key="MOUSE", mouseX=mx, mouseY=my, button=translateMouseState(state))
		except Exception:
			return InputEvent("MOUSE")
	if 1 <= raw <= 26:
		letter = chr(raw + 64)
		return InputEvent(key=letter, ctrl=True)
	if 32 <= raw <= 126:
		return InputEvent(chr(raw))
	return InputEvent(f"KEY_{raw}")