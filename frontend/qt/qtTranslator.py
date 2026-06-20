from PyQt6.QtCore import Qt
from input.event import InputEvent

def translateKey(event):
	keymap = {
		Qt.Key.Key_Left: 		"LEFT",
		Qt.Key.Key_Right: 		"RIGHT",
		Qt.Key.Key_Up: 			"UP",
		Qt.Key.Key_Down: 		"DOWN",
		Qt.Key.Key_Home: 		"HOME",
		Qt.Key.Key_End: 		"END",
		Qt.Key.Key_PageUp:		"PAGE_UP",
		Qt.Key.Key_PageDown:	"PAGE_DOWN",
		Qt.Key.Key_Backspace:	"BACKSPACE",
		Qt.Key.Key_Return:		"ENTER",
		Qt.Key.Key_Enter:		"ENTER",
		Qt.Key.Key_Tab: 		"TAB",
		Qt.Key.Key_Escape:		"ESC"
	}
	ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
	shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
	alt = bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)

	if event.key() in keymap:
		key = keymap[event.key()]
	elif ctrl and Qt.Key.Key_A <= event.key() <= Qt.Key.Key_Z:
		key = chr(event.key())
	elif ctrl and event.key() == Qt.Key.Key_BracketLeft:
		key = "["
	elif ctrl and event.key() == Qt.Key.Key_BracketRight:
		key = "]"
	elif ctrl and event.key() == Qt.Key.Key_Backslash:
		key = "\\"
	elif ctrl and event.key() == Qt.Key.Key_Slash:
		key = "/"
	elif ctrl and event.key() == Qt.Key.Key_Backspace:
		key = "BACKSPACE"
	else:
		key = event.text()

	return InputEvent(
		key=key,
		ctrl=ctrl,
		shift=shift,
		alt=alt
	)

def translateMouse(event):
	return InputEvent(
		key="MOUSE",
		mouseX=int(event.position().x()),
		mouseY=int(event.position().y()),
		button="LEFT_CLICK"
	)