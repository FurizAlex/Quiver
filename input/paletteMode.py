import os
import curses
from commands.fileCommands import openFileBuffer

def fuzzyMatch(query, text):
	query = query.lower()
	text = text.lower()
	i = 0

	for ch in text:
		if i < len(query) and ch == query[i]:
			i += 1
	return i == len(query)

def filtered(editor):
	query = editor.paletteInput.strip()

	if not query:
		return editor.paletteItems
	items = [
		item
		for item in editor.paletteItems
		if fuzzyMatch(query, item["name"])
	]
	items.sort(
		key=lambda item: (
			not item["name"].lower().startswith(query.lower()),
			len(item["name"])
		)
	)
	return items

def execute(editor):
	items = filtered(editor)

	if not items:
		return

	editor.paletteSelection = max(0, min(editor.paletteSelection, len(items) - 1))
	item = items[editor.paletteSelection]
	action = item["action"]

	if action == "quit":
		editor.running = False
	elif action == "toggle_explorer":
		editor.showExplorer = not editor.showExplorer
	elif action == "split_pane":
		from commands.uiCommands import splitPane
		
		splitPane(editor)
	elif action == "close_pane":
		from commands.uiCommands import closePane
		
		closePane(editor)
	elif action == "save_file":
		editor.saving = True
		editor.saveInput = editor.buffer.filename or ""
	elif action == "open_file":
		editor.paletteMode = "files"
		editor.paletteInput = ""
		editor.paletteSelection = 0

		items = []

		for file in sorted(os.listdir(".")):
			if os.path.isfile(file):
				items.append({"name": file, "action": "open_file_path", "path": os.path.abspath(file)})
		editor.paletteItems = items
		return
	elif action == "change_theme":
		editor.paletteMode = "themes"
		editor.paletteInput = ""
		editor.paletteSelection = 0
		editor.paletteItems = []

		for theme in editor.theme.availableThemes():
			editor.paletteItems.append({
				"name": theme["name"],
				"action": "load_theme",
				"theme": theme["id"]
			})
		return
	elif action == "close_file":
		from commands.bufferCommands import closeBuffer
		
		closeBuffer(editor)
	elif action == "open_file_path":
		openFileBuffer(editor, item["path"])

	editor.paletteOpen = False

def handle(editor, key):
	items = filtered(editor)

	if key == 27:
		editor.paletteOpen = False
		return
	elif key in (10, 13):
		execute(editor)
		return
	elif key in (curses.KEY_BACKSPACE, 127, 8):
		editor.paletteInput = editor.paletteInput[:-1]
	elif key == curses.KEY_UP:
		if items:
			editor.paletteSelection = max(0, editor.paletteSelection - 1)
	elif key == curses.KEY_DOWN:
		if items:
			editor.paletteSelection = min(len(items) - 1, editor.paletteSelection + 1)
	elif 32 <= key <= 126:
		editor.paletteInput += chr(key)
	editor.paletteSelection = min(editor.paletteSelection, max(0, len(items) - 1))

def openCommandPalette(editor):
	editor.paletteOpen = True
	editor.paletteMode = "commands"
	editor.paletteInput = ""
	editor.paletteSelection = 0
	editor.paletteItems = [
		{
			"name": "Open File",
			"action": "open_file"
		},
		{
			"name": "Save File",
			"action": "save_file"
		},
		{
			"name": "Close File",
			"action": "close_file"
		},
		{
			"name": "Change Theme",
			"action": "change_theme"
		},
		{
			"name": "Toggle Explorer",
			"action": "toggle_explorer"
		},
		{
			"name": "Split Pane",
			"action": "split_pane"
		},
		{
			"name": "Close Pane",
			"action": "close_pane"
		},
		{
			"name": "Quit",
			"action": "quit"
		},
	]

def openFilePalette(editor):
	editor.paletteOpen = True
	editor.paletteMode = "files"
	editor.paletteInput = ""
	editor.paletteSelection = 0

	items = []
	for file in sorted(os.listdir(".")):
		if os.path.isfile(file):
			items.append({
				"name": file,
				"action": "open_file_path",
				"path": os.path.abspath(file)
			})
	editor.paletteItems = items