import os
from syntax.language import Language

class LanguageRegistry:
	def __init__(self):
		self.languages = {}

	def register(self, language):
		self.languages[language.id] = language

	def get(self, languageId):
		return self.languages.get(languageId)

	def detect(self, filename):
		_, ext = os.path.splitext(filename)
		ext = ext.lower()

		for language in self.languages.values():
			if ext in language.extensions:
				return language
		return self.languages["text"]
	
	def all(self):
		return list(self.languages.values())