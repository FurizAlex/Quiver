import curses
from commands.fileCommands import openFileBuffer

def handle(editor, key):
	if key == 27:
		editor.paletteOpen = False
		return
	elif key in (10, 13):
		execute(editor)
	elif key == curses.KEY_BACKSPACE or key == 127:
		editor.paletteInput = editor.paletteInput[:-1]
	elif key == curses.KEY_UP:
		editor.paletteSelection = max(
			0,
			editor.paletteSelection - 1
		)
	elif key == curses.KEY_DOWN:
		editor.paletteSelection = min(
			len(filtered(editor)) - 1,
			editor.paletteSelection + 1
		)
	elif 32 <= key <= 126:
		editor.paletteInput += chr(key)

def filtered(editor):
	query = editor.paletteInput.lower()

	return [
		item for item in editor.paletteItems
		if query in item.lower()
	]

def execute(editor):
	items = filtered(editor)

	if not items:
		return

	choice = items[editor.paletteSelection]

	if editor.paletteMode == "files":
		openFileBuffer(editor, choice)
	elif editor.paletteMode == "commands":
		if choice == "quit":
			editor.running = False
		elif choice == "explorer":
			editor.showExplorer = (
				not editor.showExplorer
			)
		elif choice == "split pane":
			from commands.uiCommands import splitPane
			splitPane(editor)
	editor.paletteOpen = False