class Language:
	def __init__(self, name, extensions):
		self.name = name
		self.extensions = extensions

class LanguageRegistry:
	def __init__(self):
		self.languages = []

	def register(self, language):
		self.language.append(language)

	def detect(self, filename):
		import os

		_, ext = os.path.splitext(filename)
		for language in self.languages:
			if ext in language.extensions:
				return language.name
		return "text"