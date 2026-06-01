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
	item = items[editor.paletteSelection]

	if editor.paletteMode == "files":
		openFileBuffer(editor, item["path"])
	else:
		editor.commands.execute(editor, item["command"])
	editor.paletteOpen = False

def handle(editor, event):
	items = filtered(editor)
	key = event.key

	if key == "ESC":
		editor.paletteOpen = False
		return
	elif key == "ENTER":
		execute(editor)
		return
	elif key == "BACKSPACE":
		editor.paletteInput = editor.paletteInput[:-1]
	elif key == "UP":
		if items:
			editor.paletteSelection = max(0, editor.paletteSelection - 1)
	elif key == "DOWN":
		if items:
			editor.paletteSelection = min(len(items) - 1, editor.paletteSelection + 1)
	elif len(key) == 1 and not event.ctrl and not event.alt:
		editor.paletteInput += key
	editor.paletteSelection = min(editor.paletteSelection, max(0, len(items) - 1))

def openCommandPalette(editor):
	editor.paletteOpen = True
	editor.paletteMode = "commands"
	editor.paletteInput = ""
	editor.paletteSelection = 0
	editor.paletteItems = []

	for command in editor.commands.all():
		editor.paletteItems.append({
			"name": command.title,
			"command": command.name
		})

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