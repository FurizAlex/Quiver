import re

from syntax.languages import LANGUAGES

class Lexer:
	def tokenize(self, line, language):
		keywords = LANGUAGES.get(language, set())

		tokens = []
		i = 0

		while i < len(line):
			if line[i] == '#':
				tokens.append((line[i:], "comment"))
				break
			elif line[i] in {'"', "'"}:
				quote = line[i]

				j = i + 1
				while j < len(line) and line[j] != quote:
					j += 1
				j = min(j + 1, len(line))
				tokens.append((line[i:j], "string"))
				i = j
			else:
				match = re.match(r'\w+', line[i:])

				if match:
					word = match.group(0)
					tokens.append((word, "keyword"))
					i += len(word)
				else:
					tokens.append((line[i], "text"))
					i += 1
		return tokens