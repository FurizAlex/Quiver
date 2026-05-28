import os

def openFile(filename):
	if not os.path.exists(filename):
		return [""]

	try:
		with open(
			filename,
			'r',
			encoding='utf-8'
		) as f:
			return f.read().splitlines()
	except Exception as e:
		return [f"Error opening file: {e}"]

def saveFile(filename, lines):
	try:
		with open(
			filename,
			'w',
			encoding='utf-8'
		) as f:
			f.write('\n'.join(lines))
		return f"Saved {filename}"
	except Exception as e:
		return f"Error saving file: {e}"