import os

def openFile(filename):
	if not os.path.exists(filename):
		return [""]

	with open(filename, 'r') as f:
		return f.read().split_line()

def saveFile(filename, lines):
	with open(filename, 'w') as f:
		f.write('\n'.join(lines))
	return f"Saved {filename}"