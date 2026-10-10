import curses

from input.keys import *
from core.navigation import *

from commands.fileCommands import save

from commands.uiCommands import toggleExplorer
from commands.uiCommands import splitPane
from commands.uiCommands import nextPane

from commands.tabCommands import nextBuffer
from commands.tabCommands import previousBuffer
from commands.tabCommands import switchToBuffer
from commands.tabCommands import moveBuffer
from commands.tabCommands import reopenClosedBuffer
from commands.tabCommands import activeIndex

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

# Group consecutive typing into one undo step (undo removes a word, not a single character)
GROUP_TYPING_UNDO = True

OPENERS = {'(': ')', '[': ']', '{': '}'}

COMMENT_PREFIXES = {
	"python": "#", "ruby": "#", "bash": "#", "shell": "#", "sh": "#", "zsh": "#",
	"yaml": "#", "toml": "#", "makefile": "#", "perl": "#", "r": "#",
	"powershell": "#", "dockerfile": "#", "text": "#",
	"javascript": "//", "typescript": "//", "c": "//", "cpp": "//", "c++": "//",
	"csharp": "//", "c#": "//", "java": "//", "go": "//", "rust": "//",
	"swift": "//", "kotlin": "//", "php": "//", "scala": "//", "dart": "//",
	"lua": "--", "sql": "--", "haskell": "--",
	"lisp": ";", "clojure": ";", "ini": ";", "asm": ";",
}

def isWordChar(ch):
	return ch.isalnum() or ch == "_"

def markModified(editor):
	editor.pane.buffer.modified = True

def leadingWhitespace(line):
	return line[:len(line) - len(line.lstrip(" \t"))]

def indentUnit(editor):
	settings = editor.settings
	return "\t" if settings.useTabs else " " * settings.tabSize

def visualColumn(line, x, tabSize):
	col = 0
	for ch in line[:x]:
		if ch == "\t":
			col += tabSize - (col % tabSize)
		else:
			col += 1
	return col

def tabText(editor):
	"""What the Tab key inserts: a tab, or spaces up to the next tab stop."""
	settings = editor.settings
	if settings.useTabs:
		return "\t"
	pane = editor.pane
	line = pane.buffer.lines[pane.cursorY]
	col = visualColumn(line, pane.cursorX, settings.tabSize)
	return " " * (settings.tabSize - (col % settings.tabSize))

def isPython(buffer):
	return bool(buffer.language) and buffer.language.name.lower() in ("python", "py")

def autoIndent(editor, textBefore, extra=True):
	indent = leadingWhitespace(textBefore)
	stripped = textBefore.rstrip()
	if extra and stripped:
		last = stripped[-1]
		if last in OPENERS or (last == ":" and isPython(editor.pane.buffer)):
			indent += indentUnit(editor)
	return indent

def selectedLineRange(editor):
	"""Lines touched by the selection (or just the cursor line)."""
	pane = editor.pane
	selection = editor.selection
	if selection.active:
		n = selection.normalized()
		sy, ey = n["sy"], n["ey"]
		if ey > sy and n["ex"] == 0:
			ey -= 1
		return sy, ey, n
	return pane.cursorY, pane.cursorY, None

def remapAfterLineEdits(editor, edits):
	"""Keep cursor + selection stable after inserting/removing text at the start of lines.
	edits maps line -> (column, delta)."""
	pane = editor.pane
	selection = editor.selection

	def adjust(x, y):
		edit = edits.get(y)
		if not edit:
			return x
		col, delta = edit
		if delta >= 0:
			return x + delta if (x > col or (x == col and col > 0)) else x
		if x >= col - delta:
			return x + delta
		return min(x, col)

	if selection.active:
		n = selection.normalized()
		headAtEnd = (pane.cursorY, pane.cursorX) == (n["ey"], n["ex"])
		sx, sy = adjust(n["sx"], n["sy"]), n["sy"]
		ex, ey = adjust(n["ex"], n["ey"]), n["ey"]
		selection.clear()
		if headAtEnd:
			selection.begin(sx, sy)
			selection.update(ex, ey)
			pane.cursorX, pane.cursorY = ex, ey
		else:
			selection.begin(ex, ey)
			selection.update(sx, sy)
			pane.cursorX, pane.cursorY = sx, sy
	else:
		pane.cursorX = adjust(pane.cursorX, pane.cursorY)

def shiftSelectionLines(editor, dy):
	pane = editor.pane
	selection = editor.selection
	if selection.active:
		n = selection.normalized()
		headAtEnd = (pane.cursorY, pane.cursorX) == (n["ey"], n["ex"])
		a = (n["sx"], n["sy"] + dy)
		b = (n["ex"], n["ey"] + dy)
		selection.clear()
		if headAtEnd:
			selection.begin(*a)
			selection.update(*b)
			pane.cursorX, pane.cursorY = b
		else:
			selection.begin(*b)
			selection.update(*a)
			pane.cursorX, pane.cursorY = a
	else:
		pane.cursorY += dy

def indentLines(editor):
	buffer = editor.pane.buffer
	sy, ey, _ = selectedLineRange(editor)
	unit = indentUnit(editor)
	saveUndo(editor)
	edits = {}
	for y in range(sy, ey + 1):
		if sy != ey and buffer.lines[y].strip() == "":
			continue
		buffer.lines[y] = unit + buffer.lines[y]
		edits[y] = (0, len(unit))
	markModified(editor)
	remapAfterLineEdits(editor, edits)

def removableIndent(line, tabSize):
	if line.startswith("\t"):
		return 1
	count = 0
	while count < tabSize and count < len(line) and line[count] == " ":
		count += 1
	return count

def dedentLines(editor):
	buffer = editor.pane.buffer
	sy, ey, _ = selectedLineRange(editor)
	tabSize = editor.settings.tabSize
	plan = {}
	for y in range(sy, ey + 1):
		removed = removableIndent(buffer.lines[y], tabSize)
		if removed:
			plan[y] = removed
	if not plan:
		return
	saveUndo(editor)
	edits = {}
	for y, removed in plan.items():
		buffer.lines[y] = buffer.lines[y][removed:]
		edits[y] = (0, -removed)
	markModified(editor)
	remapAfterLineEdits(editor, edits)

def smartBackspaceIndent(editor):
	"""Backspace inside space-indentation removes back to the previous tab stop."""
	settings = editor.settings
	if settings.useTabs or settings.tabSize <= 1:
		return False
	pane = editor.pane
	buffer = pane.buffer
	line = buffer.lines[pane.cursorY]
	x = pane.cursorX
	if x == 0 or line[:x].strip(" ") != "":
		return False
	target = ((x - 1) // settings.tabSize) * settings.tabSize
	if x - target <= 1:
		return False
	buffer.lines[pane.cursorY] = line[:target] + line[x:]
	pane.cursorX = target
	return True

def commentPrefix(buffer):
	name = buffer.language.name.lower() if buffer.language else "text"
	return COMMENT_PREFIXES.get(name, "#")

def toggleComment(editor):
	buffer = editor.pane.buffer
	prefix = commentPrefix(buffer)
	sy, ey, _ = selectedLineRange(editor)
	lines = buffer.lines
	targets = [y for y in range(sy, ey + 1) if lines[y].strip()]
	if not targets:
		targets = [sy]
	uncomment = all(lines[y].lstrip().startswith(prefix) for y in targets)
	saveUndo(editor)
	edits = {}
	if uncomment:
		for y in targets:
			line = lines[y]
			indent = len(line) - len(line.lstrip())
			rest = line[indent + len(prefix):]
			removed = len(prefix) + (1 if rest.startswith(" ") else 0)
			lines[y] = line[:indent] + line[indent + removed:]
			edits[y] = (indent, -removed)
	else:
		indent = min(len(lines[y]) - len(lines[y].lstrip()) for y in targets)
		for y in targets:
			line = lines[y]
			lines[y] = line[:indent] + prefix + " " + line[indent:]
			edits[y] = (indent, len(prefix) + 1)
	markModified(editor)
	remapAfterLineEdits(editor, edits)

def moveLines(editor, direction):
	pane = editor.pane
	buffer = pane.buffer
	sy, ey, _ = selectedLineRange(editor)
	if direction < 0 and sy == 0:
		return
	if direction > 0 and ey >= len(buffer.lines) - 1:
		return
	saveUndo(editor)
	block = buffer.lines[sy:ey + 1]
	if direction < 0:
		buffer.lines[sy - 1:ey + 1] = block + [buffer.lines[sy - 1]]
	else:
		buffer.lines[sy:ey + 2] = [buffer.lines[ey + 1]] + block
	markModified(editor)
	shiftSelectionLines(editor, direction)

def duplicateLines(editor):
	buffer = editor.pane.buffer
	sy, ey, _ = selectedLineRange(editor)
	saveUndo(editor)
	block = list(buffer.lines[sy:ey + 1])
	buffer.lines[ey + 1:ey + 1] = block
	markModified(editor)
	shiftSelectionLines(editor, len(block))

def deleteLines(editor):
	pane = editor.pane
	buffer = pane.buffer
	sy, ey, _ = selectedLineRange(editor)
	saveUndo(editor)
	del buffer.lines[sy:ey + 1]
	if not buffer.lines:
		buffer.lines.append("")
	editor.selection.clear()
	pane.cursorY = min(sy, len(buffer.lines) - 1)
	pane.cursorX = min(pane.cursorX, len(buffer.lines[pane.cursorY]))
	markModified(editor)

def selectCurrentLine(editor):
	pane = editor.pane
	buffer = pane.buffer
	selection = editor.selection
	lastLine = len(buffer.lines) - 1
	startY = pane.cursorY
	endY = startY + 1
	if selection.active:
		n = selection.normalized()
		if n["sx"] == 0 and n["ex"] == 0 and n["ey"] > n["sy"]:
			startY, endY = n["sy"], n["ey"] + 1
	selection.clear()
	selection.begin(0, startY)
	if endY <= lastLine:
		selection.update(0, endY)
		pane.cursorX, pane.cursorY = 0, endY
	else:
		selection.update(len(buffer.lines[lastLine]), lastLine)
		pane.cursorX, pane.cursorY = len(buffer.lines[lastLine]), lastLine

def copyLineToClipboard(editor, cut):
	pane = editor.pane
	text = pane.buffer.lines[pane.cursorY] + "\n"
	SystemClipboard(editor).copy(text)
	editor._lineClipboard = text
	if cut:
		deleteLines(editor)

def insertLineBelow(editor):
	pane = editor.pane
	buffer = pane.buffer
	line = buffer.lines[pane.cursorY]
	indent = autoIndent(editor, line)
	saveUndo(editor)
	buffer.lines.insert(pane.cursorY + 1, indent)
	pane.cursorY += 1
	pane.cursorX = len(indent)
	editor.selection.clear()
	markModified(editor)
	editor.updateScroll()

def insertLineAbove(editor):
	pane = editor.pane
	buffer = pane.buffer
	indent = leadingWhitespace(buffer.lines[pane.cursorY])
	saveUndo(editor)
	buffer.lines.insert(pane.cursorY, indent)
	pane.cursorX = len(indent)
	editor.selection.clear()
	markModified(editor)
	editor.updateScroll()

def startsUndoGroup(editor, key):
	if not GROUP_TYPING_UNDO:
		return True
	pane = editor.pane
	here = (id(pane.buffer), pane.cursorY, pane.cursorX)
	if getattr(editor, "_undoGroup", None) != here:
		return True
	return key.isspace()

def canAutoPair(key, prevChar, nextChar):
	"""Only auto-close when it won't fight what the user is typing (don't, f(x), (word)...)"""
	if key in ("'", '"'):
		if isWordChar(prevChar):
			return False
	return nextChar == "" or nextChar.isspace() or nextChar in ")]}\"',;:"

class SystemClipboard:
	"""Real OS clipboard via Qt (works with other apps / Wayland / no xclip),
	falling back to the editor's own clipboard object."""
	def __init__(self, editor):
		self.editor = editor

	def copy(self, text):
		copied = False
		try:
			from PyQt6.QtWidgets import QApplication
			app = QApplication.instance()
			if app is not None:
				app.clipboard().setText(text)
				copied = True
		except ImportError:
			pass
		try:
			self.editor.clipboard.copy(text)
			copied = True
		except Exception:
			if not copied:
				raise
		self.editor.status = f"Copied {len(text)} chars"
		self.editor.statusTimer = 120

	def paste(self):
		try:
			from PyQt6.QtWidgets import QApplication
			app = QApplication.instance()
			if app is not None:
				text = app.clipboard().text()
				if text:
					return text
		except ImportError:
			pass
		try:
			return self.editor.clipboard.paste() or ""
		except Exception:
			return ""

def redispatch(editor, event, key):
	"""Handle an alternate shortcut as its standard Ctrl+<key> equivalent."""
	handle(editor, type(event)(key=key, ctrl=True, shift=False, alt=False))

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
	buffer.modified = True

def insertText(editor, text, undo=True):
	if undo:
		saveUndo(editor)
	buffer = editor.pane.buffer
	pane = editor.pane
	buffer.insertChar(pane.cursorX, pane.cursorY, text)
	buffer.modified = True
	pane.cursorX += len(text)
	editor.notifyChanged()

def handle(editor, event):
	if getattr(editor, "folderInputMode", False):
		key = event.key
		if key == "ENTER":
			import os
			path = editor.folderInput.strip()
			if os.path.isdir(path):
				editor.explorerPath = path
				editor.explorerFiles = sorted(os.listdir(path))
				editor.selectedFileIndex = 0
				editor.status = f"Folder: {path}"
			else:
				editor.status = f"Not a folder: {path}"
			editor.folderInputMode = False
			editor.folderInput = ""
			editor.statusTimer = 120
			editor.notifyChanged()
			return
		elif key == "ESC":
			editor.folderInputMode = False
			editor.folderInput = ""
			editor.notifyChanged()
			return
		elif key == "BACKSPACE":
			editor.folderInput = editor.folderInput[:-1]
			editor.notifyChanged()
			return
		elif len(key) == 1 and not event.ctrl:
			editor.folderInput += key
			editor.notifyChanged()
			return
		else:
			return
	if getattr(editor, "splitterResizeMode", False):
		key = event.key
		NUDGE = 20
		if hasattr(editor, "qtWindow"):
			splitter = editor.qtWindow.views.paneContainer.splitter
			sizes = splitter.sizes()
			if key in ("LEFT", "UP") and len(sizes) >= 2:
				sizes[0] = max(50, sizes[0] - NUDGE)
				sizes[1] = max(50, sizes[1] + NUDGE)
				splitter.setSizes(sizes)
			elif key in ("RIGHT", "DOWN") and len(sizes) >= 2:
				sizes[0] = max(50, sizes[0] + NUDGE)
				sizes[1] = max(50, sizes[1] - NUDGE)
				splitter.setSizes(sizes)
			elif key in ("ESC", "TAB"):
				editor.splitterResizeMode = False
				editor.status = ""
				window = editor.qtWindow
				panes = window.views.paneContainer.paneViews
				if panes:
					panes[editor.activePane].setFocus()
			editor.notifyChanged()
		return
		
	buffer = editor.pane.buffer
	pane = editor.pane
	selection = editor.selection
	clipboard = SystemClipboard(editor)
	key = event.key
	if not key:
		return
	if not (len(key) == 1 and not event.ctrl and not event.alt):
		editor._undoGroup = None
	if editor.completionActive:
		if key == "TAB" and not event.shift:
			acceptCompletion(editor)
			return
		elif key == "ENTER" and getattr(editor, "completionNavigated", False):
			acceptCompletion(editor)
			return
		elif key == "ESC":
			editor.completionActive = False
			editor.completions = []
			editor.notifyChanged()
			return
		elif key == "UP":
			editor.completionIndex = max(0, editor.completionIndex - 1)
			editor.completionNavigated = True
			editor.notifyChanged()
			return
		elif key == "DOWN":
			editor.completionIndex = min(len(editor.completions) - 1, editor.completionIndex + 1)
			editor.completionNavigated = True
			editor.notifyChanged()
			return
		else:
			editor.completionActive = False
			editor.completions = []
	if key == "ESC" and pane.multiCursor.isMulti():
		pane.multiCursor.collapseToPrimary()
		selection.clear()
		editor.notifyChanged()
		return
	if key == "ESC" and selection.active:
		selection.clear()
		editor.notifyChanged()
		return
	if event.ctrl and event.alt and not event.shift:
		match key.upper():
			case "UP":
				cursors = pane.multiCursor.cursors
				firstCursor = min(cursors, key=lambda c: c.y)
				targetY = firstCursor.y - 1
				if targetY >= 0:
					targetX = min(firstCursor.x, len(buffer.lines[targetY]))
					pane.multiCursor.addCursor(targetX, targetY)
				editor.notifyChanged()
				return
			case "DOWN":
				cursors = pane.multiCursor.cursors
				lastCursor = max(cursors, key=lambda c: c.y)
				targetY = lastCursor.y + 1
				if targetY < len(buffer.lines):
					targetX = min(lastCursor.x, len(buffer.lines[targetY]))
					pane.multiCursor.addCursor(targetX, targetY)
				editor.notifyChanged()
				return
			case "S":
				editor.splitterResizeMode = True
				editor.status = "RESIZE MODE: ←→ resize, ESC/TAB to exit"
				editor.notifyChanged()
				return
	if event.alt and not event.ctrl and not event.shift:
		match key.upper():
			case "UP":
				moveLines(editor, -1)
				editor.notifyChanged()
				return
			case "DOWN":
				moveLines(editor, 1)
				editor.notifyChanged()
				return
			case _ if key.isdigit() and key != "0":
				count = len(editor.buffers)
				index = count - 1 if key == "9" else int(key) - 1
				if index < count:
					switchToBuffer(editor, index)
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
			case "Z":
				if hasattr(editor, "qtWindow"):
					editor.qtWindow.toggleZenMode()
				editor.notifyChanged()
				return
			case "I":
				i = activeIndex(editor)
				if i > 0:
					moveBuffer(editor, i, i - 1)
				return
			case "O":
				i = activeIndex(editor)
				if i < len(editor.buffers) - 1:
					moveBuffer(editor, i, i + 1)
				return
			case "C":
				redispatch(editor, event, "C")
				return
			case "V":
				redispatch(editor, event, "V")
				return
			case "D":
				duplicateLines(editor)
			case "K":
				deleteLines(editor)
			case "T":
				reopenClosedBuffer(editor)
				return
			case "TAB":
				previousBuffer(editor)
				return
			case "ENTER":
				insertLineAbove(editor)
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
				if not editor.completionActive:
					editor.gotoMode = True
					editor.gotoInput = ""
			case "H":
				if hasattr(editor, "qtWindow"):
					editor.qtWindow.openDocs()
			case "D":
				saveUndo(editor)
				if not pane.multiCursor.isMulti() and not selection.active:
					line = buffer.lines[pane.cursorY]
					x = pane.cursorX
					start = x
					while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
						start -= 1
					end = x
					while end < len(line) and (line[end].isalnum() or line[end] == "_"):
						end += 1
					if start < end:
						selection.begin(start, pane.cursorY)
						selection.update(end, pane.cursorY)
						pane.cursorX = end
					editor.notifyChanged()
					return
				else:
					select = selection.normalized()
					searchText = buffer.getSelection(select["sx"], select["sy"], select["ex"], select["ey"])
					if not searchText or "\n" in searchText:
						return
					lastCursor = pane.multiCursor.cursors[-1]
					searchLine = lastCursor.y
					searchCol = lastCursor.x
					lineCount = len(buffer.lines)
					for offset in range(lineCount + 1):
						lineIndex = (searchLine + offset) % lineCount
						line = buffer.lines[lineIndex]
						fromColumn = searchCol if (offset == 0) else 0
						column = line.find(searchText, fromColumn)
						if column == -1:
							continue
						already = any(c.y == lineIndex and c.x == column + len(searchText) for c in pane.multiCursor.cursors)
						if already:
							continue
						pane.multiCursor.addCursor(column + len(searchText), lineIndex)
						selection.addSelection(column, lineIndex, column + len(searchText), lineIndex)
						pane.cursorY = lineIndex
						pane.cursorX = column + len(searchText)
						editor.updateScroll()
						editor.notifyChanged()
						return
					editor.status = "NO MORE OCCURRENCES"
					editor.statusTimer = 120
					editor.notifyChanged()
			case "E":
				if hasattr(editor, "signals"):
					if hasattr(editor, "qtWindow"):
						editor.qtWindow.focusExplorer()
				else:
					editor.focus = "explorer"
				editor.notifyChanged()
			case "F":
				if not editor.completionActive:
					editor.searchMode = True
					editor.searchInput = ""
					editor.searchMatches = []
					editor.searchMatchIndex = 0
			case "C":
				editor._lineClipboard = None
				if selection.active:
					if hasattr(selection, "allNormalized") and len(selection.allNormalized()) > 1:
						parts = []
						for select in sorted(selection.allNormalized(), key=lambda s: (s["sy"], s["sx"])):
							if select["sy"] == select["ey"]:
								parts.append(buffer.lines[select["sy"]][select["sx"]:select["ex"]])
							else:
								chunk = []
								for y in range(select["sy"], select["ey"] + 1):
									line = buffer.lines[y]
									if y == select["sy"]:
										chunk.append(line[select["sx"]:])
									elif y == select["ey"]:
										chunk.append(line[:select["ex"]])
									else:
										chunk.append(line)
								parts.append("\n".join(chunk))
						clipboard.copy('\n'.join(parts))
					else:
						selects = selection.normalized()
						lines = []
						for y in range(selects["sy"], selects["ey"] + 1):
							line = buffer.lines[y]
							if y == selects["sy"] and y == selects["ey"]:
								lines.append(line[selects["sx"]:selects["ex"]])
							elif y == selects["sy"]:
								lines.append(line[selects["sx"]:])
							elif y == selects["ey"]:
								lines.append(line[:selects["ex"]])
							else:
								lines.append(line)
						clipboard.copy("\n".join(lines))
				else:
					copyLineToClipboard(editor, False)
			case "V":
				text = clipboard.paste()
				if text:
					text = text.replace("\r\n", "\n").replace("\r", "\n")
				if text and text == getattr(editor, "_lineClipboard", None) and not selection.active and not pane.multiCursor.isMulti():
					saveUndo(editor)
					buffer.lines.insert(pane.cursorY, text[:-1])
					pane.cursorY += 1
					markModified(editor)
					editor.updateScroll()
					editor.notifyChanged()
					return
				if text:
					if selection.active:
						saveUndo(editor)
						deleteSelection(editor)
					if "\n" in text:
						saveUndo(editor)
						parts = text.split("\n")
						line = buffer.lines[pane.cursorY]
						left = line[:pane.cursorX]
						right = line[pane.cursorX:]
						buffer.lines[pane.cursorY] = left + parts[0]
						for i, part in enumerate(parts[1: -1], 1):
							buffer.lines.insert(pane.cursorY + i, part)
						lastIndex = pane.cursorY + len(parts) - 1
						buffer.lines.insert(lastIndex, parts[-1] + right)
						pane.cursorY = lastIndex
						pane.cursorX = len(parts[-1])
					else:
						insertText(editor, text)
					editor.updateScroll()
					editor.notifyChanged()
			case "X":
				editor._lineClipboard = None
				if selection.active:
					select = selection.normalized()
					text = buffer.getSelection(select["sx"], select["sy"], select["ex"], select["ey"])
					clipboard.copy(text)
					saveUndo(editor)
					deleteSelection(editor)
				else:
					copyLineToClipboard(editor, True)
			case "W":
				if hasattr(editor, "qtWindow"):
					editor.qtWindow.tabBar.closeTab(activeIndex(editor))
				else:
					editor.commands.execute("close_file", editor)
			case "T":
				if hasattr(editor, "qtWindow"):
					editor.qtWindow.newFileQt()
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
				if selection.active:
					deleteSelection(editor)
					editor.notifyChanged()
					return
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
					while i > 0 and line[i - 1] in " \t":
						i -= 1
					if i == x:
						while i > 0 and line[i - 1] not in " \t":
							i -= 1
					elif i > 0:
						while i > 0 and line[i - 1] not in " \t":
							i -= 1
					buffer.lines[pane.cursorY] = line[:i] + line[x:]
					pane.cursorX = i
				markModified(editor)
				editor.notifyChanged()
			case "DELETE":
				saveUndo(editor)
				if selection.active:
					deleteSelection(editor)
				else:
					line = buffer.lines[pane.cursorY]
					x = pane.cursorX
					if x >= len(line):
						if pane.cursorY < len(buffer.lines) - 1:
							buffer.mergeLine(pane.cursorY + 1)
					else:
						i = x
						while i < len(line) and line[i] in " \t":
							i += 1
						while i < len(line) and line[i] not in " \t":
							i += 1
						buffer.lines[pane.cursorY] = line[:x] + line[i:]
					markModified(editor)
			case "A":
				selection.begin(0, 0)
				lastLine = len(buffer.lines) - 1
				selection.update(len(buffer.lines[lastLine]), lastLine)
				pane.cursorY = lastLine
				pane.cursorX = len(buffer.lines[lastLine])
			case "/":
				toggleComment(editor)
			case "[":
				from commands.uiCommands import nextPane
				nextPane(editor)
				return
			case "]":
				from commands.uiCommands import previousPane
				previousPane(editor)
				return
			case "\\":
				from commands.uiCommands import closePane
				closePane(editor)
				return
			case "INSERT":
				redispatch(editor, event, "C")
				return
			case "TAB" | "PAGE_DOWN":
				nextBuffer(editor)
				return
			case "PAGE_UP":
				previousBuffer(editor)
				return
			case "L":
				selectCurrentLine(editor)
			case "ENTER":
				insertLineBelow(editor)
			case "HOME":
				pane.cursorY = 0
				pane.cursorX = 0
			case "END":
				pane.cursorY = len(buffer.lines) - 1
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
			case "INSERT":
				redispatch(editor, event, "V")
				return
			case "DELETE":
				redispatch(editor, event, "X")
				return
			case "TAB":
				dedentLines(editor)
			case _:
				matched = False
		if matched:
			editor.notifyChanged()
			return
	match key:
		case "TAB":
			if selection.active:
				indentLines(editor)
			elif pane.multiCursor.isMulti():
				insertTextMultiCursor(editor, indentUnit(editor))
			else:
				insertText(editor, tabText(editor))
		case "ENTER":
			if pane.multiCursor.isMulti():
				insertTextMultiCursor(editor, "\n")
				editor.updateScroll()
				editor.notifyChanged()
				return
			saveUndo(editor)
			if selection.active:
				deleteSelection(editor)
			line = buffer.lines[pane.cursorY]
			left = line[:pane.cursorX]
			right = line[pane.cursorX:]
			indent = autoIndent(editor, left)
			opener = left.rstrip()[-1:] if left.strip() else ""
			if opener in OPENERS and right.lstrip()[:1] == OPENERS[opener]:
				baseIndent = leadingWhitespace(left)
				buffer.lines[pane.cursorY] = left
				buffer.lines.insert(pane.cursorY + 1, indent)
				buffer.lines.insert(pane.cursorY + 2, baseIndent + right.lstrip())
				pane.cursorY += 1
				pane.cursorX = len(indent)
			else:
				if left.strip() == "":
					left = ""
				buffer.lines[pane.cursorY] = left
				buffer.lines.insert(pane.cursorY + 1, indent + right)
				pane.cursorY += 1
				pane.cursorX = len(indent)
			buffer.modified = True
			editor.updateScroll()
			editor.notifyChanged()
		case "BACKSPACE":
			if pane.multiCursor.isMulti():
				backspaceMultiCursor(editor)
				return
			saveUndo(editor)
			editor.completionActive = False
			editor.completions = []
			if selection.active and hasattr(selection, "allNormalized"):
				allSelects = selection.allNormalized()
				if len(allSelects) > 1:
					for select in reversed(sorted(allSelects, key=lambda s: (s["sy"], s["sx"]))):
						if select["sy"] == select["ey"]:
							line = buffer.lines[select["sy"]]
							buffer.lines[select["sy"]] = line[:select["sx"]] + line[select["ex"]:]
						else:
							first = buffer.lines[select["sy"]][:select["sx"]]
							last = buffer.lines[select["ey"]][select["ex"]:]
							buffer.lines[select["sy"]:select["ey"] + 1] = [first + last]
					first = min(allSelects, key=lambda s: (s["sy"], s["sx"]))
					pane.cursorX = first["sx"]
					pane.cursorY = first["sy"]
					selection.clear()
					editor.notifyChanged()
					return
			if selection.active:
				deleteSelection(editor)
			elif pane.cursorX > 0 and smartBackspaceIndent(editor):
				pass
			elif pane.cursorX > 0:
				line = buffer.lines[pane.cursorY]
				isCode = buffer.language and buffer.language.name.lower() != "text"
				bracketRemovalSetting = editor.settings.bracketAutoRemoveEnabled
				if isCode and bracketRemovalSetting and pane.cursorX < len(line) and line[pane.cursorX - 1] in PAIRS and line[pane.cursorX] == PAIRS[line[pane.cursorX - 1]]:
					buffer.lines[pane.cursorY] = line[:pane.cursorX - 1] + line[pane.cursorX + 1:]
					pane.cursorX -= 1
				else:
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
			if pane.multiCursor.isMulti():
				from core.multiCursor import forEachCursor
				forEachCursor(pane, moveLeft)
			else:
				moveLeft(buffer, pane)
			editor.notifyChanged()
		case "RIGHT":
			selection.clear()
			if pane.multiCursor.isMulti():
				from core.multiCursor import forEachCursor
				forEachCursor(pane, moveRight)
			else:
				moveRight(buffer, pane)
			editor.notifyChanged()
		case "UP":
			selection.clear()
			if pane.multiCursor.isMulti():
				from core.multiCursor import forEachCursor
				forEachCursor(pane, moveUp)
			else:
				moveUp(buffer, pane)
			editor.notifyChanged()
		case "DOWN":
			selection.clear()
			if pane.multiCursor.isMulti():
				from core.multiCursor import forEachCursor
				forEachCursor(pane, moveDown)
			else:
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
			if len(key) == 1 and key.isprintable() and not event.ctrl and not event.alt:
				line = buffer.lines[pane.cursorY]
				closers = set(PAIRS.values())
				if pane.multiCursor.isMulti():
					insertTextMultiCursor(editor, key)
					updateCompletions(editor) if isWordChar(key) else dismissCompletions(editor)
					editor.notifyChanged()
					return
				if key in closers and pane.cursorX < len(line) and line[pane.cursorX] == key:
					if key not in ('"', "'") or not selection.active:
						pane.cursorX += 1
						editor.notifyChanged()
						return
				if selection.active or startsUndoGroup(editor, key):
					saveUndo(editor)
				prevChar = line[pane.cursorX - 1] if pane.cursorX > 0 else ""
				nextChar = line[pane.cursorX] if pane.cursorX < len(line) else ""
				if key in PAIRS and (selection.active or canAutoPair(key, prevChar, nextChar)):
					if selection.active:
						select = selection.normalized()
						text = buffer.getSelection(select["sx"], select["sy"], select["ex"], select["ey"])
						deleteSelection(editor)
						insertText(editor, key + text + PAIRS[key], undo=False)
						pane.cursorX -= 1
					else:
						insertText(editor, key + PAIRS[key], undo=False)
						pane.cursorX -= 1
				else:
					if selection.active:
						if hasattr(selection, "allNormalized") and len(selection.allNormalized()) > 1:
							allSelects = sorted(selection.allNormalized(), key=lambda s: (s["sy"], s["sx"]), reverse=True)
							for select in allSelects:
								if select["sy"] == select["ey"]:
									line = buffer.lines[select["sy"]]
									buffer.lines[select["sy"]] = line[:select["sx"]] + key + line[select["ex"]:]
								else:
									first = buffer.lines[select["sy"]][:select["sx"]]
									last = buffer.lines[select["ey"]][select["ex"]:]
									buffer.lines[select["sy"]:select["ey"] + 1] = [first + key + last]
							lastSelect = min(allSelects, key=lambda s: (s["sy"], s["sx"]))
							pane.cursorY = lastSelect["sy"]
							pane.cursorX = lastSelect["sx"] + len(key)
							selection.clear()
							buffer.modified = True
						else:
							deleteSelection(editor)
							insertText(editor, key, undo=False)
					else:
						insertText(editor, key, undo=False)
				editor._undoGroup = (id(buffer), pane.cursorY, pane.cursorX)
				if isWordChar(key):
					updateCompletions(editor)
				else:
					dismissCompletions(editor)
				editor.notifyChanged()
				return
	editor.completionActive = False
	editor.completions = []
	editor.notifyChanged()

def insertTextMultiCursor(editor, text):
	pane = editor.pane
	buffer = pane.buffer
	cursors = pane.multiCursor.cursors

	if len(cursors) == 1:
		insertText(editor, text)
		return
	saveUndo(editor)
	hasNewline = "\n" in text
	parts = text.split("\n") if hasNewline else None
	addedLinesPerInsert = (len(parts) - 1) if hasNewline else 0

	snapshot = sorted(
		[(c, c.y, c.x) for c in cursors],
		key=lambda t: (t[1], t[2]),
		reverse=True
	)
	for cursor, originY, originX in snapshot:
		line = buffer.lines[originY]

		if hasNewline:
			left = line[:originX]
			right = line[originX:]
			buffer.lines[originY] = left + parts[0]
			for i, part in enumerate(parts[1:-1], 1):
				buffer.lines.insert(originY + i, part)
			lastIndex = originY + len(parts) - 1
			buffer.lines.insert(lastIndex, parts[-1] + right)

			cursor.x = len(parts[-1])
			cursor.y  = lastIndex

			for other, otherOriginY, otherOriginX in snapshot:
				if other is cursor:
					continue
				if otherOriginY > originY:
					other.y += addedLinesPerInsert
				elif otherOriginY == originY and otherOriginX >= originX:
					other.y = lastIndex
					other.x = otherOriginX - originX + len(parts[-1])
		else:
			buffer.lines[originY] = line[:originX] + text + line[originX:]
			cursor.x = originX + len(text)
			cursor.y = originY

			for other, otherOriginY, otherOriginX in snapshot:
				if other is cursor:
					continue
				if otherOriginY == originY and otherOriginX >= originX:
					other.x += len(text)
	pane.multiCursor.removeDuplicates()
	editor.notifyChanged()

def backspaceMultiCursor(editor):
	pane = editor.pane
	buffer = pane.buffer
	cursors = pane.multiCursor.cursors

	saveUndo(editor)
	snapshot = sorted(
		[(c, c.y, c.x) for c in cursors],
		key=lambda t: (t[1], t[2]),
		reverse=True
	)

	for cursor, originY, originX in snapshot:
		if originX > 0:
			line = buffer.lines[originY]
			buffer.lines[originY] = line[:originX - 1] + line[originX:]
			cursor.x = originX - 1
			cursor.y = originY
			for other, otherOriginY, otherOriginX in snapshot:
				if other is cursor:
					continue
				if otherOriginY == originY and otherOriginX >= originX:
					other.x -= 1
		elif originY > 0:
			prevLineLen = len(buffer.lines[originY - 1])
			buffer.lines[originY - 1] += buffer.lines[originY]
			del buffer.lines[originY]
			cursor.x = prevLineLen
			cursor.y = originY - 1

			for other, otherOriginY, otherOriginX in snapshot:
				if other is cursor:
					continue
				if otherOriginY > originY:
					other.y -= 1
				elif otherOriginY == originY:
					other.y = originY - 1
					other.x = prevLineLen + otherOriginX
	pane.multiCursor.removeDuplicates()
	editor.notifyChanged()

def dismissCompletions(editor):
	editor.completionActive = False
	editor.completions = []
	editor.completionNavigated = False

def updateCompletions(editor):
	pane = editor.pane
	line = pane.buffer.lines[pane.cursorY]
	start = pane.cursorX
	while start > 0 and isWordChar(line[start - 1]):
		start -= 1
	prefix = line[start:pane.cursorX]
	suggestions = []
	if len(prefix) >= 2:
		suggestions = [s for s in editor.completion.getSuggestions(pane.buffer, pane.cursorX, pane.cursorY) if s != prefix]
	if suggestions:
		editor.completions = suggestions
		editor.completionIndex = 0
		editor.completionNavigated = False
		editor.completionActive = True
	else:
		dismissCompletions(editor)
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
	while start > 0 and isWordChar(line[start - 1]):
		start -= 1
	saveUndo(editor)
	buffer.lines[pane.cursorY] = line[:start] + completion + line[x:]
	buffer.modified = True
	pane.cursorX = start + len(completion)
	dismissCompletions(editor)
	editor.notifyChanged()

def newFile(editor):
	# A new file is always a *new tab*, so nothing can be lost - no confirmation needed.
	createNewBuffer(editor)

def createNewBuffer(editor):
	from core.buffer import Buffer
	buffer = Buffer(editor=editor, language=editor.languageRegistry.get("text"))
	editor.buffers.append(buffer)
	switchToBuffer(editor, len(editor.buffers) - 1)
	editor.status = "NEW FILE"
	editor.statusTimer = 120
	editor.notifyChanged()

def startOrUpdateSelection(editor):
	pane = editor.pane
	selection = editor.selection

	if not selection.active:
		selection.begin(pane.cursorX, pane.cursorY)
	else:
		selection.update(pane.cursorX, pane.cursorY)
