from config.default import DEFAULT_SETTINGS

class Settings:
	def __init__(self):
		self.values = DEFAULT_SETTINGS.copy()

	def get(self, key):
		return self.values.get(key)

	def set(self, key, value):
		self.values[key] = value