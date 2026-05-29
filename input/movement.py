def moveLeft(buffer, cursor):
	if cursor.cursorX > 0:
		cursor.cursorX -= 1

	elif cursor.cursorY > 0:
		cursor.cursorY -= 1
		cursor.cursorX = len(buffer.lines[cursor.cursorY])

def moveRight(buffer, cursor):
	lineLength = len(buffer.lines[cursor.cursorY])

	if cursor.cursorX < lineLength:
		cursor.cursorX += 1

	elif cursor.cursorY < len(buffer.lines) - 1:
		cursor.cursorY += 1
		cursor.cursorX = 0

def moveUp(buffer, cursor):
	if cursor.cursorY > 0:
		cursor.cursorY -= 1

	lineLength = len(buffer.lines[cursor.cursorY])

	cursor.cursorX = min(cursor.cursorX, lineLength)

def moveDown(buffer, cursor):
	if cursor.cursorY < len(buffer.lines) - 1:
		cursor.cursorY += 1

	lineLength = len(buffer.lines[cursor.cursorY])

	cursor.cursorX = min(cursor.cursorX, lineLength)

def moveHome(buffer, cursor):
	cursor.cursorX = 0

def moveEnd(buffer, cursor):
	cursor.cursorX = len(buffer.lines[cursor.cursorY])