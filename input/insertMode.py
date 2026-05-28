import curses

from input.keys import *

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

def handle(editor, key):
	pane = editor.pane
	buffer = editor.buffer
	history = editor.history

	cursorX = pane.cursorX
	cursorY = pane.cursorY

	if key == CTRL_Q:
		editor.running = False
		return
	elif key == CTRL_S:
		save(editor)
		return
	elif key == CTRL_P:
		editor.paletteOpen = True
		editor.paletteMode = "commands"
		editor.paletteInput = ""
		editor.paletteItems = [
			"save",
			"quit",
			"split pane",
			"toggle explorer"
		]
		editor.paletteSelection = 0
		return
	elif key == CTRL_B:
		toggleExplorer(editor)
		return
	elif key == CTRL_Z:
		undo(editor)
		return
	elif key == CTRL_Y:
		redo(editor)
		return
	elif key == CTRL_O:
		editor.paletteOpen = True
		editor.paletteMode = "files"
		editor.paletteInput = ""
		editor.paletteItems = (editor.explorerFiles.copy())
		editor.paletteSelection = 0
		return
	elif key == CTRL_W:
		splitPane(editor)
		return
	elif key == TAB:
		nextPane(editor)
		return
	elif key == curses.KEY_F2:
		nextBuffer(editor)
	elif key == curses.KEY_F1:
		previousBuffer(editor)

	# -------------------------
	# MOVEMENT
	# -------------------------
	elif key == curses.KEY_LEFT:
		pane.moveLeft()
	elif key == curses.KEY_RIGHT:
		line = buffer.currentLine(cursorY)
		pane.moveRight(len(line))
	elif key == curses.KEY_UP:
		pane.moveUp()

		line = buffer.currentLine(pane.cursorY)
		pane.cursorX = min(
			pane.cursorX,
			len(line)
		) 
	elif key == curses.KEY_DOWN:
		pane.moveDown(len(buffer.lines))

		line = buffer.currentLine(pane.cursorY)
		
		pane.cursorX = min(
			pane.cursorX,
			len(line)
		)

	# -----------------------------
	# BACKSPACE
	# -----------------------------

	elif key in (
		curses.KEY_BACKSPACE,
		127,
		8
	):
		history.push(
			buffer.lines,
			pane.cursorX,
			pane.cursorY
		)
		if pane.cursorX > 0:
			buffer.deleteChar(
				pane.cursorX,
				pane.cursorY
			)
			pane.moveLeft()
		elif pane.cursorY > 0:
			prevLength = len(
				buffer.lines[pane.cursorY - 1]
			)
			buffer.mergeLine(pane.cursorY)
			pane.cursorY -= 1
			pane.cursorX = prevLength

	# ------------------------
	# ENTER
	# ------------------------

	elif key in (ENTER, 13, curses.KEY_ENTER):
		history.push(buffer.lines, pane.cursorX, pane.cursorY)
		line = buffer.currentLine(pane.cursorY)
		indent = ""

		for char in line:
			if char in (' ', '\t'):
				indent += char
			else:
				break
		
		if (pane.cursorX > 0 and line[pane.cursorX - 1] == '('):
			indent += "    "
		
		buffer.splitLine(pane.cursorX, pane.cursorY)

		buffer.lines[pane.cursorY + 1] = (
			indent + buffer.lines[pane.cursorY + 1]
		)
		pane.cursorY += 1
		pane.cursorX = len(indent)

	# ------------------------------
	# TEXT INPUT
	# ------------------------------

	elif 32 <= key <= 126:
		history.push(buffer.lines, pane.cursorX, pane.cursorY)
		
		char = chr(key)

		if char in PAIRS:
			closing = PAIRS[char]

			buffer.insertChar(pane.cursorX, pane.cursorY, char + closing)
			pane.cursorX += 1
		else:
			buffer.insertChar(pane.cursorX, pane.cursorY, char)
			pane.cursorX += 1