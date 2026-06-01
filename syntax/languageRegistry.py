import os
from syntax.language import Language

class LanguageRegistry:
	def __init__(self):
		self.languages = {}
		self.extensions = {}

	def register(self, language):
		self.languages[language.id] = language

		for ext in language.extensions:
			self.extensions[ext.lower()] = language.id

	def get(self, languageId):
		return self.languages.get(languageId)

	def detect(self, filename):
		if not filename:
			return self.get("text")
			
		_, ext = os.path.splitext(filename)
		langId = self.extensions.get(ext.lower(), "text")

		return self.get(langId)
	
	def all(self):
		return list(self.languages.values())