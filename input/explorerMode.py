import os
import curses

from commands.fileCommands import openFileBuffer

def handle(editor, key):
	if key == 9:
		editor.focus = "editor"
		return
	if key == curses.KEY_UP:
		editor.selectedFileIndex = max(0, editor.selectedFileIndex - 1)
	elif key == curses.KEY_DOWN:
		editor.selectedFileIndex = min(len(editor.explorerFiles) - 1, editor.selectedFileIndex + 1)
	elif key == 10:
		if not editor.explorerFiles:
			return
		selected = editor.explorerFiles[editor.selectedFileIndex]

		path = os.path.join(editor.explorerPath, selected)

		if os.path.isdir(path):
			editor.explorerPath = path
			editor.refreshExplorer()
			editor.selectedFileIndex = 0
		else:
			openFileBuffer(editor, path)
			editor.focus = "editor"