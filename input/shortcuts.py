from input.keys import *

def handleShortcut(editor, key):
	if key == CTRL_S:
		from commands.fileCommands import save
		save(editor)
		return True
	elif key == CTRL_P:
		editor.paletteOpen = True
		editor.paletteMode = "commands"
		return True
	return False