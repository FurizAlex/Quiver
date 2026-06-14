import os
import curses
from commands.fileCommands import openFileBuffer

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
	key = event.key

	if key == "ESC":
		editor.paletteOpen = False
		editor.paletteInput = ""
		editor.paletteMode = "commands"
		editor.notifyChanged()
		return
	if key == "UP":
		editor.paletteSelection = max(0, editor.paletteSelection - 1)
		editor.notifyChanged()
		return
	if key == "DOWN":
		items = filtered(editor)
		editor.paletteSelection = min(len(items) - 1, editor.paletteSelection + 1)
		editor.notifyChanged()
		return
	if key == "ENTER":
		items = filtered(editor)
		if not items:
			return
		select = items[min(editor.paletteSelection, len(items) - 1)]
		command = select.get("command", "")
		if editor.paletteMode == "files":
			path = select.get("path", "")
			if os.path.isdir(path):
				editor.paletteDir = path
				editor.paletteInput = ""
				editor.paletteSelection = 0
				populateFilePalette(editor, path)
				editor.notifyChanged()
				return
			else:
				openFileBuffer(editor, path)
		elif command.startswith("__theme__"):
			themeId = command[len("__theme__"):]
			applyTheme(editor, themeId)
			editor.paletteOpen = False
			editor.paletteInput = ""
			editor.notifyChanged()
			return
		elif editor.paletteMode == "commands":
			if command:
				editor.paletteOpen = False
				editor.paletteInput = ""
				editor.paletteMode = "commands"
				editor.commands.execute(editor, command)
				editor.notifyChanged()
				return
		editor.paletteOpen = False
		editor.paletteInput = ""
		editor.notifyChanged()
		return
	if key == "BACKSPACE":
		if editor.paletteInput:
			editor.paletteInput = editor.paletteInput[:-1]
		elif editor.paletteMode == "files":
			current = getattr(editor, "paletteDir", editor.explorerPath)
			parent = os.path.dirname(os.path.abspath(current))
			if parent != os.path.abspath(current):
				editor.paletteDir = parent
				populateFilePalette(editor, parent)
		editor.paletteSelection = 0
		editor.notifyChanged()
		return
	if len(key) == 1 and not event.ctrl:
		editor.paletteInput += key
		editor.paletteSelection = 0
		editor.notifyChanged()

def filtered(editor):
	query = editor.paletteInput.strip().lower()
	items = editor.paletteItems
	if not query:
		return items
	matched = [i for i in items if fuzzy(query, i["name"].lower())]
	matched.sort(key=lambda i: (not i["name"].lower().startswith(query), len(i["name"])))
	return matched

def fuzzy(query, text):
	it = 0
	for ch in text:
		if it < len(query) and ch == query[it]:
			it += 1
	return it == len(query)

def applyTheme(editor, themeId):
	import importlib
	try:
		module = importlib.import_module(f"themes.{themeId}")
	except ModuleNotFoundError:
		editor.status = f"Theme error: {themeId}"
		editor.statusTimer = 120
		return
	editor.theme.load(themeId)
	editor.currentTheme = themeId
	if hasattr(editor, "stdscr") and editor.stdscr is not None:
		editor.theme.initialize()
	if hasattr(editor, "signals"):
		from frontend.qt.amigaPalette import applyThemeToQt
		applyThemeToQt(module.THEME)
		if hasattr(editor, "qtWindow"):
			editor.qtWindow.applyQtTheme(module.THEME)
	editor.settings.set("theme", themeId)
	editor.saveConfig()
	editor.status = f"Theme: {editor.theme.metadata.get('name', themeId)}"
	editor.statusTimer = 120
	editor.notifyChanged()

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
	editor.notifyChanged()

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

def populateFilePalette(editor, path):
	items = []
	current = os.path.abspath(path)
	parent = os.path.dirname(current)

	if parent != current:
		items.append({"name": ".. (go up)", "path": parent,})
	try:
		for name in sorted(os.listdir(path)):
			fullPath = os.path.join(path, name)
			display = f"> {name}" if os.path.isdir(fullPath) else f"    {name}"
			items.append({"name": display, "path": fullPath})
	except Exception:
		pass
	editor.paletteItems = items