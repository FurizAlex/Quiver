import re

class CompletionEngine:
	WORD_RE = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b')
	MAX_SUGGESTIONS = 8

	def getSuggestions(self, buffer, cursorX, cursorY):
		line = buffer.lines[cursorY] if cursorY < len(buffer.lines) else ""
		prefix = self.prefixAt(line, cursorX)
		if len(prefix) < 2:
			return []
		
		words = self.collectWords(buffer, cursorY)
		seen = set()
		results = []
		for word in words:
			if (word.startswith(prefix) and word != prefix and word not in seen):
				seen.add(word)
				results.append(word)
			if len(results) >= self.MAX_SUGGESTIONS:
				break
		return results
	
	def prefixAt(self, line, x):
		start = x
		while start > 0 and (line[start - 1].isalnum() or line[start - 1] == '_'):
			start -= 1
		return line[start:x]
	
	def collectWords(self, buffer, currentLine):
		words = []
		lineCount = len(buffer.lines)
		visited = set()
		for dist in range(lineCount):
			for lineIndex in (currentLine - dist, currentLine + dist):
				if lineIndex in visited or lineIndex < 0 or lineIndex >= lineCount:
					continue
				visited.add(lineIndex)
				for match in self.WORD_RE.finditer(buffer.lines[lineIndex]):
					words.append(match.group())
		return words