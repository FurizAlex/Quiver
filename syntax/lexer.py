import re

from syntax.languages import LANGUAGES

class Lexer:
	def tokenize(self, line, language):
		keywords = LANGUAGES.get(language, set())

		tokens = []
		i = 0

		while i < len(line):
			if line[i] == '#':
				tokens.append((line[i:], 3))
				break
			elif line[i] in {'"', "'"}:
				quote = line[i]

				j = i + 1
				while j < len(line) and line[j] != quote:
					j += 1
				j = min(j + 1, len(line))
				tokens.append((line[i:j], 2))
				i = j
			else:
				match = re.match(r'\w+', line[i:])

				if match:
					word = match.group(0)
					color = 1 if word in keywords else 4
					tokens.append((word, color))
					i += len(word)
				else:
					tokens.append((line[i], 4))
					i += 1
		return tokens