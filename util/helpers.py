import re

def nextWordStart(line, pos):
	match = re.search(r'\w\w*', line[pos + 1:])

	if match:
		return pos + 1 + match.start()

	return len(line)

def nextWordEnd(line, pos):
	match = re.search(r'\w\w*', line[pos + 1:])

	if match:
		return pos + 1 + match.start()
	
	return len(line)

def prevWordStart(line, pos):
	for i in range(pos - 1, -1, -1):
		if re.match(r'\w', line[i]):
			if i == 0 or not re.match(r'\w', line[i - 1]):
				return i
	return 0