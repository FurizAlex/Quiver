local curses = require "curses"

-- == Initalizaer == --
curses.initscr()
curses.cbreak()
curses.echo(false)
curses.nl(false)

local stdscr = curses.stdscr()

stdscr:keypad(true)
stdscr:nodelay(false)

local buffer = {""}
local cursorX, cursorY = 1, 1
local mode = "NORMAL"
local status = "-- Welcome to Quiver --"
local running = true

-- == Helper == --

local function drawScreen()
	stdscr:clear()
	for i, line in ipairs(buffer) do
		stdscr:mvaddstr(i - 1, 0, line)
	end
	
	local maxY = #buffer
	local maxX = #buffer[cursorY] or ""

	stdscr:mvaddstr(curses.LINES - 1, 0, ("-- %s -- %s"):format(mode, status))
	stdscr:move(cursorY - 1, cursorX - 1)
	stdscr:refresh()
end

local function clampCursor()
	local lineLen = #buffer[cursorY] or ""

	cursorY = math.max(1, math.min(#buffer, cursorY))
	cursorX = math.max(1, math.min(lineLen + 1, cursorX))
end

local function insertChar(c)
	local line = buffer[cursorY]
	local before = line:sub(1, cursorX - 1)
	local after = line:sub(cursorX)

	buffer[cursorY] = before .. c .. after
	cursorX = cursorX + 1
end

local function backspace()
	local line = buffer[cursorY]
	local prevline = buffer[cursorY - 1]
	local currentLine = table.remove(buffer, cursorY)

	if cursorX > 1 then
		buffer[cursorY] = line:sub(1, cursorX - 2) .. line:sub(cursorX)
		cursorX = cursorX - 1
	elseif cursorY > 1 then
		cursorY = cursorY - 1
		cursorX = #prevline + 1
		buffer[cursorY] = prevline .. currentLine
	end
end

local function newLine()
	local line = buffer[cursorY]
	local before = line:sub(1, cursorX - 1)
	local after = line:sub(cursorX)

	buffer[cursorY] = before
	table.insert(buffer, cursorY + 1, after)

	cursorY = cursorY + 1
	cursorX = 1
end

-- == Main == --

while running do
	drawScreen()
	local ch = stdscr:getch()

	if mode == "NORMAL" then
		if ch == 27 then
			mode = "NORMAL"
		elseif ch == string.byte("i") then
			mode = "INSERT"
		elseif ch == string.byte(":") then
			status = "Command: (q = quit)"
			drawScreen()
			local cmd = stdscr:getch()
			if cmd == string.byte("q") then
				running = false
			end

		elseif ch == curses.KEY_UP then
			cursorY = cursorY - 1
		elseif ch == curses.KEY_DOWN then
			cursorY = cursorY + 1
		elseif ch == curses.KEY_LEFT then
			cursorX = cursorX - 1
		elseif ch == curses.KEY_RIGHT then
			cursorX = cursorX + 1
		end

	elseif mode == "INSERT" then
		if ch == 27 then -- ESC
			mode = "NORMAL"
		elseif ch == curses.KEY_BACKSPACE or ch == 127 then
			backspace()
		elseif ch == 10 then -- Enter
			newLine()
		elseif ch >= 32 and ch <= 126 then
			insertChar(string.char(ch))
		end
	end
	clampCursor()
end

curses.endwin()