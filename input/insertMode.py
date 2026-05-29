import curses

from input.keys import *
from input.movement import *
from input.shortcuts import handleShortcut

from commands.fileCommands import save

from commands.uiCommands import toggleExplorer
from commands.uiCommands import splitPane
from commands.uiCommands import nextPane

from commands.bufferCommands import nextBuffer
from commands.bufferCommands import previousBuffer

from commands.editCommands import undo
from commands.editCommands import redo

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
	buffer = editor.buffer
	cursor = editor.cursor

	buffer.insertChar(cursor.cursorX, cursor.cursorY, text)
	cursor.cursorX += len(text)

def isBackspace(key):
	return key in (8, 127, curses.KEY_BACKSPACE)

def handle(editor, key):
	buffer = editor.buffer
	cursor = editor.cursor
	selection = editor.selection
	clipboard = editor.clipboard

	if key == CTRL_S:
		from commands.fileCommands import save

		save(editor)
		return
	elif key == CTRL_O:
		editor.paletteOpen = True
		editor.paletteMode = "files"
		try:
			import os

			editor.paletteItems = sorted(os.listdir("."))
		except:
			editor.paletteItems = []
		editor.paletteInput = ""
		editor.paletteSelection = 0
		return
	elif key == CTRL_P:
		editor.paletteOpen = True
		editor.paletteMode = "commands"
		editor.paletteItems = [
			"open",
			"save",
			"quit",
			"theme",
			"explorer",
			"split pane",
			"new buffer"
		]
		editor.paletteInput = ""
		editor.paletteSelection = 0
		return
	elif key == CTRL_N:
		from commands.bufferCommands import nextBuffer

		nextBuffer(editor)
		return
	elif key == CTRL_B:
		from commands.bufferCommands import previousBuffer

		previousBuffer(editor)
		return
	if key == 3:
		if selection.active:
			sx, sy, ex, ey = selection.normalized()

			text = buffer.getSelection(sx, sy, ex, ey)
			clipboard.copy(text)
	elif key == 24:
		if selection.active:
			sx, sy, ex, ey = selection.normalized()

			text = buffer.getSelection(sx, sy, ex, ey)
			clipboard.copy(text)
			deleteSelection(editor)
	elif key == 22:
		text = clipboard.paste()
		if text:
			insertText(editor, text)
	elif key == 9:
		insertText(editor, "\t")
	elif key == 10:
		line = buffer.lines[cursor.cursorY]

		left = line[:cursor.cursorX]
		right = line[cursor.cursorX:]

		buffer.lines[cursor.cursorY] = left
		buffer.lines.insert(cursor.cursorY + 1, right)

		cursor.cursorY += 1
		cursor.cursorX = 0
	elif key in (curses.KEY_BACKSPACE, 127):
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
	elif key == curses.KEY_LEFT:
		moveLeft(buffer, cursor)
	elif key == curses.KEY_RIGHT:
		moveRight(buffer, cursor)
	elif key == curses.KEY_UP:
		moveUp(buffer, cursor)
	elif key == curses.KEY_DOWN:
		moveDown(buffer, cursor)
	elif key == curses.KEY_HOME:
		moveHome(buffer, cursor)
	elif key == curses.KEY_END:
		moveEnd(buffer, cursor)
	elif 32 <= key <= 126:
		char = chr(key)
		
		if selection.active:
			deleteSelection(editor)
		if char in PAIRS:
			insertText(editor, char + PAIRS[char])
			cursor.cursorX -= 1
		else:
			insertText(editor, char)
			