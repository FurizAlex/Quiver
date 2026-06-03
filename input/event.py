from dataclasses import dataclass

@dataclass
class InputEvent:
	key: str
	ctrl: bool = False
	shift: bool = False
	alt: bool = False

	mouseX: int = -1
	mouseY: int = -1

	button: str | None = None