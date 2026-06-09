def visualWidth(text, tabSize):
	width = 0

	for ch in text:
		if ch == "\t":
			width += tabSize - (width % tabSize)
		else:
			width += 1
	return width