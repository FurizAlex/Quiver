from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def loadQtTheme(name):
	qss = ROOT / "themes" / f"{name}.qss"

	with open(qss, "r", encoding="utf-8") as f:
		return f.read()