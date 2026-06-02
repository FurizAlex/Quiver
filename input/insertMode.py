import curses

from input.keys import *
from input.shortcuts import handleShortcut
from input.keymap import KEYMAP

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

	buffer = editor.buffer
	sx, sy, ex, ey = selection.normalized()

	if sy == ey:
		line = buffer.lines[sy]

		buffer.lines[sy] = (line[:sx] + line[ex:])
	else:
		first = buffer.lines[sy][:sx]
		last = buffer.lines[ey][ex:]
		
		buffer.lines[sy:ey + 1] = [
			first + last
		]
	editor.cursor.cursorX = sx
	editor.cursor.cursorY = sy
	selection.clear()

def insertText(editor, text):
	saveUndo(editor)
	buffer = editor.buffer
	cursor = editor.cursor

	buffer.insertChar(cursor.cursorX, cursor.cursorY, text)
	cursor.cursorX += len(text)

	editor.status = repr(buffer.lines[cursor.cursorY])

def isBackspace(key):
	return key in (8, 127, curses.KEY_BACKSPACE)

def handle(editor, event):
	buffer = editor.buffer
	cursor = editor.cursor
	selection = editor.selection
	clipboard = editor.clipboard
	key = event.key
	command = KEYMAP.get(key)

	if command:
		editor.commands.execute(command, editor)
		return
	elif event.ctrl and key == "O":
		from input.paletteMode import openFilePalette

		openFilePalette(editor)
		return
	elif event.ctrl and key == "P":
		from input.paletteMode import openCommandPalette

		openCommandPalette(editor)
		return
	elif event.ctrl and key == "G":
		editor.gotoMode = True
		editor.gotoInput = ""
		return
	elif event.ctrl and key == "F":
		editor.searchMode = True
		editor.searchInput = ""
		return
	if key == "HOME":
		if selection.active:
			sx, sy, ex, ey = selection.normalized()

			text = buffer.getSelection(sx, sy, ex, ey)
			clipboard.copy(text)
	elif key == "END":
		if selection.active:
			sx, sy, ex, ey = selection.normalized()

			text = buffer.getSelection(sx, sy, ex, ey)
			clipboard.copy(text)
			deleteSelection(editor)
	elif key == "":
		text = clipboard.paste()
		if text:
			insertText(editor, text)
	elif key == "TAB":
		insertText(editor, "\t")
	elif key == "ENTER":
		saveUndo(editor)
		line = buffer.lines[cursor.cursorY]

		left = line[:cursor.cursorX]
		right = line[cursor.cursorX:]
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

		buffer.lines[cursor.cursorY] = left
		buffer.lines.insert(cursor.cursorY + 1, indent + right)

		cursor.cursorY += 1
		cursor.cursorX = len(indent)
	elif key == "BACKSPACE":
		saveUndo(editor)
		if selection.active:
			deleteSelection(editor)
		elif cursor.cursorX > 0:
			buffer.deleteChar(cursor.cursorX, cursor.cursorY)
			cursor.cursorX -= 1
		elif cursor.cursorY > 0:
			prev = len(buffer.lines[cursor.cursorY - 1])
			buffer.mergeLine(cursor.cursorY)
			
			cursor.cursorY -= 1
			cursor.cursorX = prev
	elif event.shift and key == "LEFT":
		startOrUpdateSelection(editor)
		moveLeft(buffer, cursor)
		selection.update(cursor.cursorX, cursor.cursorY)
	elif event.shift and key == "RIGHT":
		startOrUpdateSelection(editor)
		moveRight(buffer, cursor)
		selection.update(cursor.cursorX, cursor.cursorY)
	#elif key == curses.KEY_SHIFT_UP:
	#	startOrUpdateSelection(editor)
	#	moveUp(buffer, cursor)
	#	selection.update(cursor.cursorX, cursor.cursorY)
	#elif key == curses.KEY_SHIFT_DOWN:
	#	startOrUpdateSelection(editor)
	#	moveDown(buffer, cursor)
	#	selection.update(cursor.cursorX, cursor.cursorY)
	elif key == "LEFT":
		selection.clear()
		moveLeft(buffer, cursor)
	elif key == "RIGHT":
		selection.clear()
		moveRight(buffer, cursor)
	elif key == "UP":
		selection.clear()
		moveUp(buffer, cursor)
	elif key == "DOWN":
		selection.clear()
		moveDown(buffer, cursor)
	#elif key == KEY_CTRL_SHIFT_LEFT:
	#	startOrUpdateSelection(editor)
	#	cursor.cursorX = prevWordStart(buffer.lines[cursor.cursorY], cursor.cursorX)
	#	selection.update(cursor.cursorX, cursor.cursorY)
	#elif key == KEY_CTRL_SHIFT_RIGHT:
	#	startOrUpdateSelection(editor)
	#	cursor.cursorX = nextWordStart(buffer.lines[cursor.cursorY], cursor.cursorX)
	#	selection.update(cursor.cursorX, cursor.cursorY)
	elif key == "HOME":
		moveHome(buffer, cursor)
	elif key == "END":
		moveEnd(buffer, cursor)
	elif len(key) == 1 and not event.ctrl and not event.alt:
		saveUndo(editor)
		if key in PAIRS:
			insertText(editor, key + PAIRS[key])
			cursor.cursorX -= 1
		else:
			insertText(editor, key)
			
def startOrUpdateSelection(editor):
	cursor = editor.cursor
	selection = editor.selection

	if not selection.active:
		selection.begin(cursor.cursorX, cursor.cursorY)
	else:
		selection.update(cursor.cursorX, cursor.cursorY)