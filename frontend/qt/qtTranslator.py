from PyQt6.QtCore import Qt
from input.event import InputEvent

def translateKey(event):
	text = event.text()

	keymap = {
		Qt.Key.Key_Left: "LEFT",
		Qt.Key.Key_Right: "RIGHT",
		Qt.Key.Key_Up: "UP",
		Qt.Key.Key_Down: "DOWN",

		Qt.Key.Key_Home: "HOME",
		Qt.Key.Key_End: "END",

		Qt.Key.Key_Backspace: "BACKSPACE",

		Qt.Key.Key_Return: "ENTER",
		Qt.Key.Key_Enter: "ENTER",

		Qt.Key.Key_Tab: "TAB",

		Qt.Key.Key_Escape: "ESC"
	}
	key = keymap.get(event.key(), text)
	return InputEvent(
		key=key,
		ctrl=bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier),
		shift=bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier),
		alt=bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
	)

def translateMouse(event):
	return InputEvent(
		key="MOUSE",
		mouseX=int(event.position().x()),
		mouseY=int(event.position().y()),
		button="LEFT_CLICK"
	)