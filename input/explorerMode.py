import os
import curses

from commands.fileCommands import openFileBuffer

def handle(editor, event):
	key = event.key
	
	if key == "TAB":
		editor.focus = "editor"
		return
	if key == "UP":
		editor.selectedFileIndex = max(0, editor.selectedFileIndex - 1)
	elif key == "DOWN":
		editor.selectedFileIndex = min(len(editor.explorerFiles) - 1, editor.selectedFileIndex + 1)
	elif key == "BACKSPACE":
		parent = os.path.dirname(editor.explorerPath)
		if parent != editor.explorerPath:
			editor.explorerPath = parent
			editor.refreshExplorer()
			editor.selectedFileIndex = 0
	elif key == "ENTER":
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