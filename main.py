import os
import curses

from core.editor import Editor

def main(stdscr):
	os.system("stty -ixon")
	editor = Editor(stdscr)
	editor.run()

if __name__ == "__main__":
    curses.wrapper(main)