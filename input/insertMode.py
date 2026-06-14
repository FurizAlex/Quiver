import curses

from input.keys import *
from core.navigation import *

from commands.fileCommands import save

from commands.uiCommands import toggleExplorer
from commands.uiCommands import splitPane
from commands.uiCommands import nextPane

from commands.bufferCommands import nextBuffer
from commands.bufferCommands import previousBuffer

from commands.editCommands import undo
from commands.editCommands import redo
from commands.historyCommands import saveUndo

PAIRS = {
	'(': ')',
	'[': ']',
	'{': '}',
	'"': '"',
	"'": "'"
}

def deleteSelection(editor):
	selection = editor.selection

	if not selection.active:
		return

	buffer = editor.pane.buffer
	sel = selection.normalized()
	sx = sel["sx"]
	sy = sel["sy"]
	ex = sel["ex"]
	ey = sel["ey"]

	if sy == ey:
		line = buffer.lines[sy]
		buffer.lines[sy] = (line[:sx] + line[ex:])
	else:
		first = buffer.lines[sy][:sx]
		last = buffer.lines[ey][ex:]
		buffer.lines[sy:ey + 1] = [first + last]
	editor.pane.cursorX = sx
	editor.pane.cursorY = sy
	selection.clear()

def insertText(editor, text):
	saveUndo(editor)
	buffer = editor.pane.buffer
	pane = editor.pane
	buffer.insertChar(pane.cursorX, pane.cursorY, text)
	pane.cursorX += len(text)
	editor.notifyChanged()

def handle(editor, event):
	buffer = editor.pane.buffer
	pane = editor.pane
	selection = editor.selection
	clipboard = editor.clipboard
	key = event.key

	if editor.completionActive:
		if key == "TAB" or key == "ENTER":
			acceptCompletion(editor)
			return
		elif key == "ESC":
			editor.completionActive = False
			editor.completions = []
			editor.notifyChanged()
			return
		elif key == "UP":
			editor.completionIndex = max(0, editor.completionIndex - 1)
			editor.notifyChanged()
			return
		elif key == "DOWN":
			editor.completionIndex = min(len(editor.completions) - 1, editor.completionIndex + 1)
			editor.notifyChanged()
			return
	if event.ctrl and event.shift:
		match key.upper():
			case "LEFT":
				startOrUpdateSelection(editor)
				moveWordLeft(buffer, pane)
				selection.update(pane.cursorX, pane.cursorY)
			case "RIGHT":
				startOrUpdateSelection(editor)
				moveWordRight(buffer, pane)
				selection.update(pane.cursorX, pane.cursorY)
			case "UP":
				startOrUpdateSelection(editor)
				moveUp(buffer, pane)
				selection.update(pane.cursorX, pane.cursorY)
			case "DOWN":
				startOrUpdateSelection(editor)
				moveDown(buffer, pane)
				selection.update(pane.cursorX, pane.cursorY)
		editor.notifyChanged()
		return
	if event.ctrl and not event.shift:
		match key.upper():
			case "S":
				save(editor)
			case "Z":
				undo(editor)
			case "Y":
				redo(editor)
			case "N":
				nextBuffer(editor)
			case "B":
				previousBuffer(editor)
			case "O":
				from input.paletteMode import openFilePalette
				openFilePalette(editor)
			case "P":
				from input.paletteMode import openCommandPalette
				openCommandPalette(editor)
			case "G":
				editor.gotoMode = True
				editor.gotoInput = ""
			case "D":
				saveUndo(editor)
				if not selection.active:
					line = buffer.lines[pane.cursorY]
					x = pane.cursorX
					start = x
					while start > 0 and (line[start - 1].isalnum or line[start - 1] == '_'):
						start -= 1
					end = x
					while end < len(line) and (line[end].isalnum() or line[end] == '_'):
						end += 1
					if start < end:
						selection.begin(start, pane.cursorY)
						selection.update(end, pane.cursorY)
						pane.cursorX = end
					editor.notifyChanged()
				else:
					select = selection.normalized()
					searchText = buffer.getSelection(select["sx"], select["sy"], select["ex"], select["ey"])
					if not searchText or "\n" in searchText:
						editor.notifyChanged()
						return
					startLine = select["ey"]
					startCol = select["ex"]
					found = False
					lineCount = len(buffer.lines)
					for offset in range(lineCount + 1):
						lineIndex = (startLine + offset) % lineCount
						line = buffer.lines[lineIndex]
						searchFrom = startCol if (offset == 0) else 0
						col = line.find(searchText, searchFrom)
						if col != -1 and not (lineIndex == select["sy"] and col == select["sx"]):
							selection.begin(col, lineIndex)
							selection.update(col + len(searchText), lineIndex)
							pane.cursorY = lineIndex
							pane.cursorX = col + len(searchText)
							editor.updateScroll()
							found = True
							break
					if not found:
						editor.status = "NO MORE OCCURRENCES"
						editor.statusTimer = 60
					editor.notifyChanged()
			case "E":
				if hasattr(editor, "signals"):
					if hasattr(editor, "qtWindow"):
						editor.qtWindow.focusExplorer()
				else:
					editor.focus = "explorer"
				editor.notifyChanged()
			case "F":
				editor.searchMode = True
				editor.searchInput = ""
			case "C":
				if selection.active:
					select = selection.normalized()
					text = buffer.getSelection(select["sx"], select["sy"], select["ex"], select["ey"])
					clipboard.copy(text)
			case "V":
				text = clipboard.paste()
				if text:
					if selection.active:
						deleteSelection(editor)
					insertText(editor, text)
			case "X":
				if selection.active:
					select = selection.normalized()
					text = buffer.getSelection(select["sx"], select["sy"], select["ex"], select["ey"])
					clipboard.copy(text)
					deleteSelection(editor)
			case "W":
				editor.commands.execute("close_file", editor)
			case "T":
				if hasattr(editor, "newFileQt"):
					editor.newFileQt()
				elif getattr(editor, "newFileConfirm", False):
					createNewBuffer(editor)
				else:
					newFile(editor)
			case "LEFT":
				moveWordLeft(buffer, pane)
				selection.clear()
				editor.notifyChanged()
			case "RIGHT":
				moveWordRight(buffer, pane)
				selection.clear()
				editor.notifyChanged()
			case "BACKSPACE":
				saveUndo(editor)
				line = buffer.lines[pane.cursorY]
				x = pane.cursorX
				if x == 0:
					if pane.cursorY > 0:
						prev = len(buffer.lines[pane.cursorY - 1])
						buffer.mergeLine(pane.cursorY)
						pane.cursorY -= 1
						pane.cursorX = prev
				else:
					i = x
					while i > 0 and line[i - 1] in "\t":
						i -= 1
					while i > 0 and line[i - 1] not in " \t":
						i -= 1
					buffer.lines[pane.cursorY] = line[:i] + line[x:]
					pane.cursorX = i
				editor.notifyChanged()
			case "A":
				selection.begin(0, 0)
				lastLine = len(buffer.lines) - 1
				selection.update(len(buffer.lines[lastLine]), lastLine)
			case "D":
				saveUndo(editor)
				line = buffer.lines[pane.cursorY]
				buffer.lines.insert(pane.cursorY + 1, line)
				pane.cursorY += 1
			case "/":
				saveUndo(editor)
				line = buffer.lines[pane.cursorY]
				stripped = line.lstrip()
				indent = line[:len(line) - len(stripped)]
				if stripped.startswith("#"):
					buffer.lines[pane.cursorY] = indent + stripped[1:].lstrip()
				else:
					buffer.lines[pane.cursorY] = indent + "# " + stripped
			case "HOME":
				pane.cursorY = 0
				pane.cursorX = 0
			case "END":
				pane.cursorX = len(buffer.lines) - 1
				pane.cursorX = len(buffer.lines[pane.cursorY])
			case _:
				pass
		editor.notifyChanged()
		return
	if event.shift and not event.ctrl:
		matched = True
		match key:
			case "LEFT":
				startOrUpdateSelection(editor)
				moveLeft(buffer, pane)
				selection.update(pane.cursorX, pane.cursorY)
			case "RIGHT":
				startOrUpdateSelection(editor)
				moveRight(buffer, pane)
				selection.update(pane.cursorX, pane.cursorY)
			case "UP":
				startOrUpdateSelection(editor)
				moveUp(buffer, pane)
				selection.update(pane.cursorX, pane.cursorY)
			case "DOWN":
				startOrUpdateSelection(editor)
				moveDown(buffer, pane)
				selection.update(pane.cursorX, pane.cursorY)
			case _:
				matched = False
		if matched:
			editor.notifyChanged()
			return
	match key:
		case "TAB":
			if selection.active:
				saveUndo(editor)
				select = selection.normalized()
				for y in range(select["sy"], select["ey"] + 1):
					if editor.settings.useTabs:
						buffer.lines[y] = "\t" + buffer.lines[y]
					else:
						buffer.lines[y] = " " * editor.settings.tabSize + buffer.lines[y]
			else:
				if editor.settings.useTabs:
					insertText(editor, "\t")
				else:
					insertText(editor, " " * editor.settings.tabSize)
		case "ENTER":
			saveUndo(editor)
			line = buffer.lines[pane.cursorY]
			left = line[:pane.cursorX]
			right = line[pane.cursorX:]
			indent = ""
			for ch in left:
				if ch in (" ", "\t"):
					indent += ch
				else:
					break
			if line.rstrip().endswith(":"):
				if editor.settings.useTabs:
					indent += "\t"
				else:
					indent += " " * editor.settings.tabSize
			buffer.lines[pane.cursorY] = left
			buffer.lines.insert(pane.cursorY + 1, indent + right)
			pane.cursorY += 1
			pane.cursorX = len(indent)
			editor.updateScroll()
			editor.notifyChanged()
		case "BACKSPACE":
			saveUndo(editor)
			editor.completionActive = False
			editor.completions = []
			if selection.active:
				deleteSelection(editor)
			elif pane.cursorX > 0:
				buffer.deleteChar(pane.cursorX, pane.cursorY)
				pane.cursorX -= 1
			elif pane.cursorY > 0:
				prev = len(buffer.lines[pane.cursorY - 1])
				buffer.mergeLine(pane.cursorY)
				pane.cursorY -= 1
				pane.cursorX = prev
			editor.notifyChanged()
		case "DELETE":
			saveUndo(editor)
			if selection.active:
				deleteSelection(editor)
			else:
				line = buffer.lines[pane.cursorY]
				if pane.cursorX < len(line):
					buffer.lines[pane.cursorY] = line[:pane.cursorX] + line[pane.cursorX + 1:]
				elif pane.cursorY < len(buffer.lines) - 1:
					buffer.mergeLine(pane.cursorY + 1)
			editor.notifyChanged()
		case "PAGE_UP":
			visibleHeight = editor.layout.paneVisibleHeight()
			pane.cursorY = max(0, pane.cursorY - visibleHeight)
			pane.cursorX = min(pane.cursorX, len(buffer.lines[pane.cursorY]))
			editor.updateScroll()
			editor.notifyChanged()
		case "PAGE_DOWN":
			visibleHeight = editor.layout.paneVisibleHeight()
			pane.cursorY = min(len(buffer.lines) - 1, pane.cursorY + visibleHeight)
			pane.cursorX = min(pane.cursorX, len(buffer.lines[pane.cursorY]))
			editor.updateScroll()
			editor.notifyChanged()
		case "LEFT":
			selection.clear()
			moveLeft(buffer, pane)
			editor.notifyChanged()
		case "RIGHT":
			selection.clear()
			moveRight(buffer, pane)
			editor.notifyChanged()
		case "UP":
			selection.clear()
			moveUp(buffer, pane)
			editor.notifyChanged()
		case "DOWN":
			selection.clear()
			moveDown(buffer, pane)
			editor.notifyChanged()
		case "HOME":
			line = buffer.lines[pane.cursorY]
			firstNonWS = len(line) - len(line.lstrip())
			if pane.cursorX == firstNonWS:
				pane.cursorX = 0
			else:
				pane.cursorX = firstNonWS
			editor.notifyChanged()
		case "END":
			moveEnd(buffer, pane)
			editor.notifyChanged()
		case _:
			if len(key) == 1 and not event.ctrl and not event.alt and key not in PAIRS.values():
				saveUndo(editor)
				line = buffer.lines[pane.cursorY]
				closers = set(PAIRS.values())
				if (key in closers and pane.cursorX < len(line) and line[pane.cursorX] == key):
					pane.cursorX += 1
				if key in PAIRS:
					if selection.active:
						select = selection.normalized()
						text = buffer.getSelection(select["sx"], select["sy"], select["ex"], select["ey"])
						deleteSelection(editor)
						insertText(editor, key + text + PAIRS[key])
						pane.cursorX -= 1
					else:
						insertText(editor, key + PAIRS[key])
						pane.cursorX -= 1
				else:
					insertText(editor, key)
				updateCompletions(editor)
				editor.notifyChanged()
				return
	editor.completionActive = False
	editor.completions = []
	editor.notifyChanged()

def updateCompletions(editor):
	pane = editor.pane
	suggestions = editor.completion.getSuggestions(pane.buffer, pane.cursorX, pane.cursorY)
	if suggestions:
		editor.completions = suggestions
		editor.completionIndex = 0
		editor.completionActive = True
	else:
		editor.completionActive = False
		editor.completions = []
	editor.notifyChanged()

def acceptCompletion(editor):
	if not editor.completions:
		editor.completionActive = False
		return
	pane = editor.pane
	buffer = pane.buffer
	completion = editor.completions[editor.completionIndex]
	line = buffer.lines[pane.cursorY]
	x = pane.cursorX
	start = x
	while start > 0 and (line[start - 1].isalnum() or line[start - 1] == '_'):
		start -= 1
	buffer.lines[pane.cursorY] = line[:start] + completion + line[x:]
	pane.cursorX = start + len(completion)
	editor.completionActive = False
	editor.completions = []
	editor.notifyChanged()

def newFile(editor):
	if editor.pane.buffer.modified:
		editor.pendingAction = "new_file"
		editor.status = "Wait! You haven't saved yet! Pressing Ctrl+T again will confirm a new file, ESC to cancel"
		editor.statusTimer = 180
		editor.newFileConfirm = True
		editor.notifyChanged()
		return
	createNewBuffer(editor)

def createNewBuffer(editor):
	from core.buffer import Buffer
	buffer = Buffer(editor=editor, language=editor.languageRegistry.get("text"))
	editor.buffers.append(buffer)
	newIndex = len(editor.buffers) - 1
	editor.currentBuffer = newIndex
	editor.pane.buffer = buffer
	editor.pane.cursorX = 0
	editor.pane.cursorY = 0
	editor.status = "NEW FILE"
	editor.statusTimer = 120
	editor.newFileConfirm = False
	editor.notifyChanged()
			
def startOrUpdateSelection(editor):
	pane = editor.pane
	selection = editor.selection

	if not selection.active:
		selection.begin(pane.cursorX, pane.cursorY)
	else:
		selection.update(pane.cursorX, pane.cursorY)