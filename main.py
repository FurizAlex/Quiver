import os
import curses

from core.editor import Editor

def main(stdscr):
	editor = Editor(stdscr)
	editor.run()
	
if __name__ == "__main__":
    curses.wrapper(main)