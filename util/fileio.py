import os

def openFile(filename):
	if not os.path.exists(filename):
		return [""]
	try:
		with open(filename, 'r', encoding='utf-8') as f:
			lines = f.read().splitlines()
			if not lines:
				return [""]
			return lines
	except UnicodeDecodeError:
		raise
	except Exception as e:
		raise

def saveFile(filename, lines):
	try:
		filename = os.path.abspath(filename)
		os.makedirs(os.path.dirname(filename), exist_ok=True) if os.path.dirname(filename) else None
		with open(
			filename,
			'w',
			encoding='utf-8'
		) as f:
			f.write('\n'.join(lines))
		return f"Saved {filename}"
	except Exception as e:
		return f"Error saving file: {e}"
	