from dataclasses import dataclass

@dataclass
class InputEvent:
	key: str
	ctrl: bool = False
	shift: bool = False
	alt: bool = False