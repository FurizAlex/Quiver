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
		
		buffer.lines[sy:ey + 1] = [
			first + last
		]
	editor.pane.cursorX = sx
	editor.pane.cursorY = sy
	selection.clear()

def insertText(editor, text):
	saveUndo(editor)
	buffer = editor.pane.buffer
	pane = editor.pane

	buffer.insertChar(pane.cursorX, pane.cursorY, text)
	pane.cursorX += len(text)

	editor.status = repr(buffer.lines[pane.cursorY])
	editor.notifyChanged()

def isBackspace(key):
	return key in (8, 127, curses.KEY_BACKSPACE)

def handle(editor, event):
	buffer = editor.pane.buffer
	pane = editor.pane
	selection = editor.selection
	clipboard = editor.clipboard
	key = event.key

	if event.ctrl:
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
				editor.notifyChanged()
			case "P":
				from input.paletteMode import openCommandPalette
				openCommandPalette(editor)
				editor.notifyChanged()
			case "G":
				editor.gotoMode = True
				editor.gotoInput = ""
			case "F":
				editor.searchMode = True
				editor.searchInput = ""
			case "C":
				if selection.active:
					sel = selection.normalized()
					text = buffer.getSelection(sel["sx"], sel["sy"], sel["ex"], sel["ey"])
					clipboard.copy(text)
			case "V":
				text = clipboard.paste()
				if text:
					insertText(editor, text)
			case "X":
				if selection.active:
					sel = selection.normalized()
					text = buffer.getSelection(sel["sx"], sel["sy"], sel["ex"], sel["ey"])
					clipboard.copy(text)
					deleteSelection(editor)
			case "W":
				editor.commands.execute("close_file", editor)
			case _:
				pass
		editor.notifyChanged()
		return
	elif key == "TAB":
		insertText(editor, "\t")
	elif key == "ENTER":
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
		editor.notifyChanged()
	elif key == "BACKSPACE":
		saveUndo(editor)
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
	elif event.shift and key == "LEFT":
		startOrUpdateSelection(editor)
		moveLeft(buffer, pane)
		selection.update(pane.cursorX, pane.cursorY)
	elif event.shift and key == "RIGHT":
		startOrUpdateSelection(editor)
		moveRight(buffer, pane)
		selection.update(pane.cursorX, pane.cursorY)
	#elif key == curses.KEY_SHIFT_UP:
	#	startOrUpdateSelection(editor)
	#	moveUp(buffer, pane)
	#	selection.update(pane.cursorX, pane.cursorY)
	#elif key == curses.KEY_SHIFT_DOWN:
	#	startOrUpdateSelection(editor)
	#	moveDown(buffer, pane)
	#	selection.update(pane.cursorX, pane.cursorY)
	elif key == "LEFT":
		selection.clear()
		moveLeft(buffer, pane)
		editor.notifyChanged()
	elif key == "RIGHT":
		selection.clear()
		moveRight(buffer, pane)
		editor.notifyChanged()
	elif key == "UP":
		selection.clear()
		moveUp(buffer, pane)
		editor.notifyChanged()
	elif key == "DOWN":
		selection.clear()
		moveDown(buffer, pane)
		editor.notifyChanged()
	#elif key == KEY_CTRL_SHIFT_LEFT:
	#	startOrUpdateSelection(editor)
	#	pane.cursorX = prevWordStart(buffer.lines[pane.cursorY], pane.cursorX)
	#	selection.update(pane.cursorX, pane.cursorY)
	#elif key == KEY_CTRL_SHIFT_RIGHT:
	#	startOrUpdateSelection(editor)
	#	pane.cursorX = nextWordStart(buffer.lines[pane.cursorY], pane.cursorX)
	#	selection.update(pane.cursorX, pane.cursorY)
	elif key == "HOME":
		moveHome(buffer, pane)
		editor.notifyChanged()
	elif key == "END":
		moveEnd(buffer, pane)
		editor.notifyChanged()
	elif len(key) == 1 and not event.ctrl and not event.alt:
		saveUndo(editor)
		if key in PAIRS:
			insertText(editor, key + PAIRS[key])
			pane.cursorX -= 1
		else:
			insertText(editor, key)
		editor.notifyChanged()
			
def startOrUpdateSelection(editor):
	pane = editor.pane
	selection = editor.selection

	if not selection.active:
		selection.begin(pane.cursorX, pane.cursorY)
	else:
		selection.update(pane.cursorX, pane.cursorY)