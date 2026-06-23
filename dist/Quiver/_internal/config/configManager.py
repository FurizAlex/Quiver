import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = str(PROJECT_ROOT / "config.json")

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
		except Exception as e:
			print(f"Config save error: {e}")

	def get(self, key, default=None):
		return self.data.get(key, default)

	def set(self, key, value):
		self.data[key] = value