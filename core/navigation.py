def moveLeft(buffer, cursor):
	if cursor.cursorX > 0:
		cursor.cursorX -= 1
	elif cursor.cursorY > 0:
		cursor.cursorY -= 1
		cursor.cursorX = len(buffer.lines[cursor.cursorY])

def moveRight(buffer, cursor):
	line = buffer.lines[cursor.cursorY]

	if cursor.cursorX < len(line):
		cursor.cursorX += 1
	elif cursor.cursorY < len(buffer.lines) - 1:
		cursor.cursorY += 1
		cursor.cursorX = 0

def moveUp(buffer, cursor):
	if cursor.cursorY > 0:
		cursor.cursorY -= 1
	line = buffer.lines[cursor.cursorY]

	cursor.cursorX = min(cursor.cursorX, len(line))

def moveDown(buffer, cursor):
	if cursor.cursorY < len(buffer.lines) - 1:
		cursor.cursorY += 1
	line = buffer.lines[cursor.cursorY]

	cursor.cursorX = min(cursor.cursorX, len(line))

def moveHome(buffer, cursor):
	cursor.cursorX = 0

def moveEnd(buffer, cursor):
	cursor.cursorX = len(buffer.lines[cursor.cursorY])

def moveWordLeft(buffer, cursor):
	line = buffer.lines[cursor.cursorY]
	i = cursor.cursorX

	while i > 0 and line[i - 1].isspace():
		i -= 1
	while i > 0 and not line[i - 1].isspace():
		i -= 1
	cursor.cursorX = i

def moveWordRight(buffer, cursor):
	line = buffer.lines[cursor.cursorY]
	i = cursor.cursorX

	while i < len(line) and not line[i].isspace():
		i += 1
	while i < len(line) and line[i].isspace():
		i += 1
	cursor.cursorX = i