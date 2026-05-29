from config.default import DEFAULT_SETTINGS

class Settings:
	def __init__(self):
		self.tabSize = 4
		self.useTabs = True
		
		self.showLineNumbers = True
		self.relativeLineNumbers = False

		self.autoIndent = True
		self.highlightCurrentLine = True

		self.mouseSupport = True
		self.wrapText = False

		self.cursorBlink = False

	def get(self, key):
		return self.values.get(key)

	def set(self, key, value):
		self.values[key] = value