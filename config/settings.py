from config.default import DEFAULT_SETTINGS

class Settings:
	def __init__(self):
		self.values = DEFAULT_SETTINGS.copy()

	def get(self, key):
		return self.values.get(key)

	def set(self, key, value):
		self.values[key] = value

	def load(self, config):
		for key, value in config.items():
			self.values[key] = value

	def export(self):
		return self.values.copy()

	@property
	def tabSize(self):
		return self.values.get("tab_width", 4)

	@property
	def useTabs(self):
		return self.values.get("use_tabs", True)
	
	@property
	def showLineNumbers(self):
		return self.values.get("line_numbers", True)

	@property
	def relativeLineNumbers(self):
		return self.values.get("relative_numbers", False)

	@property
	def autoIndent(self):
		return self.values.get("auto_indent", True)

	@property
	def wrapText(self):
		return self.values.get("wrap_text", False)