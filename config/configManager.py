import json
import os

CONFIG_FILE = "config.json"

class ConfigManager:
	def __init__(self):
		self.data = {}

	def load(self):
		if not os.path.exists(CONFIG_FILE):
			self.data = {}
			return
		try:
			with open(CONFIG_FILE, "r", encoding="utf-8") as f:
				self.data = json.load(f)
		except Exception:
			self.data = {}

	def save(self):
		try:
			with open(CONFIG_FILE, "w", encoding="utf-8") as f:
				json.dump(self.data, f, indent=4)
		except Exception:
			pass

	def get(self, key, default=None):
		return self.data.get(key, default)

	def set(self, key, value):
		self.data[key] = value